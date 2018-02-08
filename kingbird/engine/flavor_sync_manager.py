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


class FlavorSyncManager(object):
    """Manages tasks related to resource management."""

    def __init__(self, *args, **kwargs):
        super(FlavorSyncManager, self).__init__()

    def create_resources_in_region(self, job_id, force, region,
                                   source_flavor, session, context,
                                   access_tenants=None):
        """Create resources using threads."""
        target_nova_client = NovaClient(region, session)
        try:
            target_nova_client.create_flavor(force, source_flavor,
                                             access_tenants)
            LOG.info('Flavor %(flavor)s created in %(region)s'
                     % {'flavor': source_flavor.name, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id,
                                            consts.JOB_SUCCESS)
            except exceptions.JobNotFound():
                raise
        except Exception as exc:
            LOG.error('Exception Occurred: %(msg)s in %(region)s'
                      % {'msg': exc.message, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id,
                                            consts.JOB_FAILURE)
            except exceptions.JobNotFound():
                raise
            pass

    def resource_sync(self, context, job_id, force, jobs):
        """Create resources in target regions.

        Flavor with same name is created in target_regions.If a user
        wants to syncs the same resource then nova throws 409 error
        because the name is already used. In order to avoid that we
        use --force and there by creates resource without fail.

        :param context: request context object.
        :param job_id: ID of the job which triggered image_sync.
        :force: True/False option to sync the same resource again.
        :jobs: List of resource_sync_id's for param job_id.
        """
        LOG.info("Triggered Flavor Sync.")
        flavors_thread = list()
        access_tenants = None
        session = EndpointCache().get_session_from_token(
            context.auth_token, context.project)
        for job in jobs:
            try:
                resource_job = db_api.resource_sync_list(context, job_id,
                                                         job)
                resource_job = resource_job.pop()
            except exceptions.JobNotFound():
                raise
            # Create Source Region object
            source_nova_client = NovaClient(
                resource_job["source_region"], session)
            source_flavor = source_nova_client.get_flavor(
                resource_job["resource"])
            if not source_flavor.is_public:
                access_tenants = source_nova_client.\
                    get_flavor_access_tenant(resource_job["resource"])
            thread = threading.Thread(
                target=self.create_resources_in_region,
                args=(resource_job["id"], force,
                      resource_job["target_region"],
                      source_flavor, session, context, access_tenants))
            flavors_thread.append(thread)
            thread.start()
            for flavor_thread in flavors_thread:
                flavor_thread.join()

            # Update Result in DATABASE.
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
