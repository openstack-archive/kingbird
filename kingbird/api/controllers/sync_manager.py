# Copyright (c) 2017 Ericsson AB
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

import restcomm

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import uuidutils

import collections
import pecan
from pecan import expose
from pecan import request

from kingbird.common import consts
from kingbird.common.i18n import _
from kingbird.db.sqlalchemy import api as db_api
from kingbird.drivers.openstack import sdk
from kingbird.rpc import client as rpc_client

CONF = cfg.CONF

rpc_api_cap_opt = cfg.StrOpt('kb-engine',
                             help='Set a version cap for messages sent to'
                                  'kb-engine services. If you plan to do a'
                                  'live upgrade from an old version to a'
                                  'newer version, you should set this option'
                                  'to the old version before beginning the'
                                  'live upgrade procedure. Only upgrading'
                                  'to the next version is supported, so you'
                                  'cannot skip a release for the live upgrade'
                                  'procedure.')
CONF.register_opt(rpc_api_cap_opt, 'upgrade_levels')

LOG = logging.getLogger(__name__)


class SyncController(object):
    VERSION_ALIASES = {
        'Newton': '1.0',
    }

    def __init__(self, *args, **kwargs):
        super(SyncController, self).__init__(*args, **kwargs)
        self.rpc_client = rpc_client.EngineClient()

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project, action):
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        result = collections.defaultdict(dict)
        if action == 'list' or action == 'active':
            result['job_set'] = db_api.\
                sync_job_list(context, action)
        # Only admin_user can view all the sync_jobs
        elif action == 'all':
            if not context.is_admin:
                pecan.abort(401, _('Unauthorized'))
            result['job_set'] = db_api.\
                sync_all_job_list(context, action)
        elif uuidutils.is_uuid_like(action):
            result['job_set'] = db_api.\
                resource_sync_list_by_job(context, action)
        else:
            pecan.abort(400, _('Invalid request URL'))
        return result

    @index.when(method='POST', template='json')
    def post(self, project):
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        if not request.body:
            pecan.abort(400, _('Body required'))
        payload = eval(request.body)
        payload = payload.get('resource_set')
        if not payload:
            pecan.abort(400, _('resource_set required'))
        target_regions = payload.get('target')
        if not target_regions:
            pecan.abort(400, _('Target regions required'))
        source_region = payload.get('source')
        if not source_region:
            pecan.abort(400, _('Source region required'))
        if payload.get('resource_type') == consts.KEYPAIR:
            user_id = context.user
            source_keys = payload.get('resources')
            if not source_keys:
                pecan.abort(400, _('Source keypairs required'))
            # Create Source Region object
            source_os_client = sdk.OpenStackDriver(source_region)
            # Check for keypairs in Source Region
            for source_keypair in source_keys:
                source_keypair = source_os_client.get_keypairs(user_id,
                                                               source_keypair)
                if not source_keypair:
                    pecan.abort(404)
            job_id = uuidutils.generate_uuid()
            # Insert into the parent table
            result = db_api.sync_job_create(context, job_id=job_id)
            # Insert into the child table
            for region in target_regions:
                for keypair in source_keys:
                    db_api.resource_sync_create(context, result,
                                                region, keypair,
                                                payload.get('resource_type'))
            return self._keypair_sync(job_id, user_id, payload, context,
                                      result)
        else:
            pecan.abort(400, _('Bad resource_type'))

    @index.when(method='delete', template='json')
    def delete(self, project, job_id):
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project) or project != context.project:
            pecan.abort(400, _('Invalid request URL'))
        if uuidutils.is_uuid_like(job_id):
            status = db_api.sync_job_status(context, job_id)
            if status == 'IN_PROGRESS':
                pecan.abort(406, _('action not supported'
                                   ' while sync is in progress'))
            db_api.sync_job_delete(context, job_id)
            return 'job %s deleted from the database.' % job_id
        else:
            pecan.abort(400, _('Bad request'))

    def _keypair_sync(self, job_id, user_id, payload, context, result):
        self.rpc_client.keypair_sync_for_user(context, job_id, payload,
                                              user_id)

        return {'job_status': {'id': result.id, 'status': result.sync_status,
                               'updated_at': result.updated_at}}
