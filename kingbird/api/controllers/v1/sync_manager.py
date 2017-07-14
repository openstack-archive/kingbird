# Copyright (c) 2017 Ericsson AB.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from oslo_utils import uuidutils

import collections
import pecan
from pecan import expose
from pecan import request

from kingbird.api.controllers import restcomm
from kingbird.common import consts
from kingbird.common.endpoint_cache import EndpointCache
from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.db.sqlalchemy import api as db_api
from kingbird.drivers.openstack.glance_v2 import GlanceClient
from kingbird.drivers.openstack.nova_v2 import NovaClient
from kingbird.rpc import client as rpc_client


LOG = logging.getLogger(__name__)


class ResourceSyncController(object):
    VERSION_ALIASES = {
        'Newton': '1.0',
    }

    def __init__(self, *args, **kwargs):
        super(ResourceSyncController, self).__init__(*args, **kwargs)
        self.rpc_client = rpc_client.EngineClient()

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    def _entries_to_database(self, context, target_regions, source_region,
                             resources, resource_type, job_id):
        """Manage the entries to database for both Keypair and image."""
        # Insert into the parent table
        try:
            result = db_api.sync_job_create(context, job_id=job_id)
        except exceptions.InternalError:
            pecan.abort(500, _('Internal Server Error.'))
            # Insert into the child table
        for region in target_regions:
            for resource in resources:
                try:
                    db_api.resource_sync_create(context, result,
                                                region, source_region,
                                                resource, resource_type)
                except exceptions.JobNotFound:
                    pecan.abort(404, _('Job not found'))
        return result

    @index.when(method='GET', template='json')
    def get(self, project, action=None):
        """Get details about Sync Job.

        :param project: It's UUID of the project.
        :param action: Optional. If provided, it can be
            'active' to get the list of active jobs.
            'job-id' to get the details of a job.
        """
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        result = collections.defaultdict(dict)
        if not action or action == 'active':
            result['job_set'] = db_api.sync_job_list(context, action)
        elif uuidutils.is_uuid_like(action):
            try:
                result['job_set'] = db_api.resource_sync_list_by_job(
                    context, action)
            except exceptions.JobNotFound:
                pecan.abort(404, _('Job not found'))
        else:
            pecan.abort(400, _('Invalid request URL'))
        return result

    @index.when(method='POST', template='json')
    def post(self, project):
        """Sync resources present in one region to another region.

        :param project: It's UUID of the project.
        """
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        payload = eval(request.body)
        if not payload:
            pecan.abort(400, _('Body required'))
        payload = payload.get('resource_set')
        if not payload:
            pecan.abort(400, _('resource_set required'))
        resource_type = payload.get('resource_type')
        target_regions = payload.get('target')
        if not target_regions or not isinstance(target_regions, list):
            pecan.abort(400, _('Target regions required'))
        source_region = payload.get('source')
        if not source_region or not isinstance(source_region, str):
            pecan.abort(400, _('Source region required'))
        source_resources = payload.get('resources')
        if not source_resources:
            pecan.abort(400, _('Source resources required'))
        job_id = uuidutils.generate_uuid()
        if resource_type == consts.KEYPAIR:
            session = EndpointCache().get_session_from_token(
                context.auth_token, context.project)
            # Create Source Region object
            source_nova_client = NovaClient(source_region, session)
            # Check for keypairs in Source Region
            for source_keypair in source_resources:
                source_keypair = source_nova_client.\
                    get_keypairs(source_keypair)
                if not source_keypair:
                    pecan.abort(404)
            result = self._entries_to_database(context, target_regions,
                                               source_region,
                                               source_resources,
                                               resource_type, job_id)
            return self._keypair_sync(job_id, payload, context, result)

        elif resource_type == consts.IMAGE:
            # Create Source Region glance_object
            glance_driver = GlanceClient(source_region, context)
            # Check for images in Source Region
            for image in source_resources:
                source_image = glance_driver.check_image(image)
                if image != source_image:
                    pecan.abort(404)
            result = self._entries_to_database(context, target_regions,
                                               source_region,
                                               source_resources,
                                               resource_type, job_id)
            return self._image_sync(job_id, payload, context, result)
        else:
            pecan.abort(400, _('Bad resource_type'))

    @index.when(method='delete', template='json')
    def delete(self, project, job_id):
        """Delete the database entries of a given job_id.

        :param project: It's UUID of the project.
        :param job_id: ID of the job for which the database entries
            have to be deleted.
        """
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        if uuidutils.is_uuid_like(job_id):
            try:
                status = db_api.sync_job_status(context, job_id)
            except exceptions.JobNotFound:
                pecan.abort(404, _('Job not found'))
            if status == consts.JOB_PROGRESS:
                pecan.abort(406, _('action not supported'
                                   ' while sync is in progress'))
            try:
                db_api.sync_job_delete(context, job_id)
            except exceptions.JobNotFound:
                pecan.abort(404, _('Job not found'))
            return 'job %s deleted from the database.' % job_id
        else:
            pecan.abort(400, _('Bad request'))

    def _keypair_sync(self, job_id, payload, context, result):
        """Make an rpc call to kb-engine.

        :param job_id: ID of the job to update values in database based on
            the job_id.
        :param payload: payload object.
        :param context: context of the request.
        :param result: Result object to return an output.
        """
        self.rpc_client.keypair_sync_for_user(context, job_id, payload)

        return {'job_status': {'id': result.id, 'status': result.sync_status,
                               'created_at': result.created_at}}

    def _image_sync(self, job_id, payload, context, result):
        """Make an rpc call to engine.

        :param job_id: ID of the job to update values in database based on
            the job_id.
        :param payload: payload object.
        :param context: context of the request.
        :param result: Result object to return an output.
        """
        self.rpc_client.image_sync(context, job_id, payload)
        return {'job_status': {'id': result.id, 'status': result.sync_status,
                               'created_at': result.created_at}}
