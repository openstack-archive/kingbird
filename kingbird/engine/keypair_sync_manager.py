# Copyright 2017 Ericsson AB.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading

from oslo_log import log as logging

from kingbird.common import consts
from kingbird.common.endpoint_cache import EndpointCache
from kingbird.common import exceptions
from kingbird.db.sqlalchemy import api as db_api
from kingbird.drivers.openstack.nova_v2 import NovaClient

LOG = logging.getLogger(__name__)


class KeypairSyncManager(object):
    """Manages tasks related to resource management."""

    def __init__(self, *args, **kwargs):
        super(KeypairSyncManager, self).__init__()

    def create_resources_in_region(self, job_id, force, target_regions,
                                   source_keypair, session, context):
        """Create Region specific threads."""
        regions_thread = list()
        for region in target_regions:
            thread = threading.Thread(target=self.create_resources,
                                      args=(job_id, force, region,
                                            source_keypair, session,
                                            context))
            regions_thread.append(thread)
            thread.start()
            for region_thread in regions_thread:
                region_thread.join()

    def create_resources(self, job_id, force, region, source_keypair,
                         session, context):
        """Create resources using threads."""
        target_nova_client = NovaClient(region, session)
        try:
            target_nova_client.create_keypairs(force, source_keypair)
            LOG.info('keypair %(keypair)s created in %(region)s'
                     % {'keypair': source_keypair.name, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id, region,
                                            source_keypair.name,
                                            consts.JOB_SUCCESS)
            except exceptions.JobNotFound():
                raise
        except Exception as exc:
            LOG.error('Exception Occurred: %(msg)s in %(region)s'
                      % {'msg': exc.message, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id, region,
                                            source_keypair.name,
                                            consts.JOB_FAILURE)
            except exceptions.JobNotFound():
                raise
            pass

    def resource_sync(self, context, job_id, payload):
        """Create resources in target regions.

        :param context: request context object.
        :param job_id: ID of the job which triggered image_sync.
        :payload: request payload.
        """
        LOG.info("Triggered Keypair Sync.")
        keypairs_thread = list()
        target_regions = payload['target']
        force = eval(str(payload.get('force', False)))
        resource_ids = payload.get('resources')
        source_region = payload['source']
        session = EndpointCache().get_session_from_token(
            context.auth_token, context.project)
        # Create Source Region object
        source_nova_client = NovaClient(source_region, session)
        for keypair in resource_ids:
            source_keypair = source_nova_client.get_keypairs(keypair)
            thread = threading.Thread(target=self.create_resources_in_region,
                                      args=(job_id, force, target_regions,
                                            source_keypair, session,
                                            context,))
            keypairs_thread.append(thread)
            thread.start()
            for keypair_thread in keypairs_thread:
                keypair_thread.join()
        try:
            resource_sync_details = db_api.\
                resource_sync_status(context, job_id)
        except exceptions.JobNotFound:
            raise
        result = consts.JOB_SUCCESS
        if consts.JOB_FAILURE in resource_sync_details:
            result = consts.JOB_FAILURE
        try:
            db_api.sync_job_update(context, job_id, result)
        except exceptions.JobNotFound:
            raise
