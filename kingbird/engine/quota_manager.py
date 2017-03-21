# Copyright 2016 Ericsson AB
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

import collections
from Queue import Queue
import re
import threading
import time

from oslo_config import cfg
from oslo_log import log as logging

from kingbird.common import consts
from kingbird.common import context
from kingbird.common import endpoint_cache
from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.common import manager
from kingbird.common import utils
from kingbird.db import api as db_api
from kingbird.drivers.openstack import sdk
from kingbird.engine import kingbird_lock

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# Projects are synced batch by batch. Below configuration defines
# number of projects in each batch
batch_opts = [
    cfg.IntOpt('batch_size',
               default=3,
               help='Batch size number of projects will be synced at a time')
]

batch_opt_group = cfg.OptGroup('batch')
cfg.CONF.register_group(batch_opt_group)
cfg.CONF.register_opts(batch_opts, group=batch_opt_group)
TASK_TYPE = 'quota_sync'


class QuotaManager(manager.Manager):
    """Manages tasks related to quota management"""

    def __init__(self, *args, **kwargs):
        LOG.debug(_('QuotaManager initialization...'))

        super(QuotaManager, self).__init__(service_name="quota_manager",
                                           *args, **kwargs)
        self.context = context.get_admin_context()
        self.endpoints = endpoint_cache.EndpointCache()

    def periodic_balance_all(self, engine_id):
        LOG.info("periodically balance quota for all keystone tenants")
        lock = kingbird_lock.sync_lock_acquire(self.context, engine_id,
                                               TASK_TYPE)
        if not lock:
            LOG.error("Not able to acquire lock for %(task_type)s, may"
                      " be Previous sync job has not finished yet, "
                      "Aborting this run at: %(time)s ",
                      {'task_type': TASK_TYPE,
                       'time': time.strftime("%c")}
                      )
            return
        LOG.info("Successfully acquired lock")
        projects_thread_list = []
        # Iterate through project list and call sync project for each project
        # using threads
        project_list = sdk.OpenStackDriver().get_enabled_projects()
        # Divide list of projects into batches and perfrom quota sync
        # for one batch at a time.
        for current_batch_projects in utils.get_batch_projects(
                cfg.CONF.batch.batch_size, project_list):
            LOG.info("Syncing quota for current batch with projects: %s",
                     current_batch_projects)
            for current_project in current_batch_projects:
                if current_project:
                    thread = threading.Thread(
                        target=self.quota_sync_for_project,
                        args=(current_project,))
                    projects_thread_list.append(thread)
                    thread.start()
                # Wait for all the threads to complete
                # the job(sync all projects quota)
                for current_thread in projects_thread_list:
                    current_thread.join()
        kingbird_lock.sync_lock_release(self.context, engine_id, TASK_TYPE)

    def read_quota_usage(self, project_id, region, usage_queue):
        # Writes usage dict to the Queue in the following format
        # {'region_name': (<nova_usages>, <neutron_usages>, <cinder_usages>)}
        LOG.info("Reading quota usage for %(project_id)s in %(region)s",
                 {'project_id': project_id,
                  'region': region}
                 )
        os_client = sdk.OpenStackDriver(region)
        region_usage = os_client.get_resource_usages(project_id)
        total_region_usage = collections.defaultdict(dict)
        # region_usage[0], region_usage[1], region_usage[3] are
        # nova, neutron & cinder usages respectively
        total_region_usage.update(region_usage[0])
        total_region_usage.update(region_usage[1])
        total_region_usage.update(region_usage[2])
        usage_queue.put({region: total_region_usage})

    def get_summation(self, regions_dict):
        # Adds resources usages from different regions
        single_region = {}
        resultant_dict = collections.Counter()
        for current_region in regions_dict:
            single_region[current_region] = collections.Counter(
                regions_dict[current_region])
            resultant_dict += single_region[current_region]
        return resultant_dict

    def _get_kingbird_project_limit(self, project_id):
        # Returns kingbird project limit for a project.
        kingbird_limits_for_project = collections.defaultdict(dict)
        try:
            # checks if there are any quota limit in DB for a project
            limits_from_db = db_api.quota_get_all_by_project(self.context,
                                                             project_id)
        except exceptions.ProjectQuotaNotFound:
            limits_from_db = {}
        for current_resource in CONF.kingbird_global_limit.iteritems():
            resource = re.sub('quota_', '', current_resource[0])
            # If resource limit in DB, then use it or else use limit
            # from conf file
            if resource in limits_from_db:
                kingbird_limits_for_project[resource] = limits_from_db[
                    resource]
            else:
                kingbird_limits_for_project[resource] = current_resource[1]
        return kingbird_limits_for_project

    def _arrange_quotas_by_service_name(self, region_new_limit):
        # Returns a dict of resources with limits arranged by service name
        resource_with_service = collections.defaultdict(dict)
        resource_with_service['nova'] = collections.defaultdict(dict)
        resource_with_service['cinder'] = collections.defaultdict(dict)
        resource_with_service['neutron'] = collections.defaultdict(dict)
        for limit in region_new_limit:
            if limit in consts.NOVA_QUOTA_FIELDS:
                resource_with_service['nova'].update(
                    {limit: region_new_limit[limit]})
            elif limit in consts.CINDER_QUOTA_FIELDS:
                resource_with_service['cinder'].update(
                    {limit: region_new_limit[limit]})
            elif limit in consts.NEUTRON_QUOTA_FIELDS:
                resource_with_service['neutron'].update(
                    {limit: region_new_limit[limit]})
        return resource_with_service

    def update_quota_limits(self, project_id, region_new_limit,
                            current_region):
        # Updates quota limit for a project with new calculated limit
        os_client = sdk.OpenStackDriver(current_region)
        os_client.write_quota_limits(project_id, region_new_limit)

    def quota_sync_for_project(self, project_id):
        # Sync quota limits for the project according to below formula
        # Global remaining limit = Kingbird global limit - Summation of usages
        #                          in all the regions
        # New quota limit = Global remaining limit + usage in that region
        LOG.info("Quota sync Called for Project: %s",
                 project_id)
        regions_thread_list = []
        # Retrieve regions for the project
        region_lists = sdk.OpenStackDriver().get_all_regions_for_project(
            project_id)
        regions_usage_dict = self.get_tenant_quota_usage_per_region(project_id)
        if not regions_usage_dict:
            # Skip syncing for the project if not able to read regions usage
            LOG.error("Error reading regions usage for the Project: '%s'. "
                      "Aborting, continue with next project.", project_id)
            return
        total_project_usages = dict(self.get_summation(regions_usage_dict))
        kingbird_global_limit = self._get_kingbird_project_limit(project_id)
        global_remaining_limit = collections.Counter(
            kingbird_global_limit) - collections.Counter(total_project_usages)

        for current_region in region_lists:
            region_new_limit = dict(
                global_remaining_limit + collections.Counter(
                    regions_usage_dict[current_region]))
            region_new_limit = self._arrange_quotas_by_service_name(
                region_new_limit)
            thread = threading.Thread(target=self.update_quota_limits,
                                      args=(project_id, region_new_limit,
                                            current_region,))
            regions_thread_list.append(thread)
            thread.start()

        # Wait for all the threads to update quota
        for current_thread in regions_thread_list:
            current_thread.join()

    def get_tenant_quota_usage_per_region(self, project_id):
        # Return quota usage dict with keys as region name & values as usages.
        # Calculates the usage from each region concurrently using threads.

        # Retrieve regions for the project
        region_lists = sdk.OpenStackDriver().get_all_regions_for_project(
            project_id)
        usage_queue = Queue()
        regions_usage_dict = collections.defaultdict(dict)
        regions_thread_list = []
        for current_region in region_lists:
            thread = threading.Thread(target=self.read_quota_usage,
                                      args=(project_id, current_region,
                                            usage_queue))
            regions_thread_list.append(thread)
            thread.start()
        # Wait for all the threads to finish reading usages
        for current_thread in regions_thread_list:
            current_thread.join()
        # Check If all the regions usages are read
        if len(region_lists) == usage_queue.qsize():
            for i in range(usage_queue.qsize()):
                # Read Queue
                current_region_data = usage_queue.get()
                regions_usage_dict.update(current_region_data)
        return regions_usage_dict

    def get_total_usage_for_tenant(self, project_id):
        # Returns total quota usage for a tenant
        LOG.info("Get total usage called for project: %s",
                 project_id)
        try:
            total_usage = dict(self.get_summation(
                self.get_tenant_quota_usage_per_region(project_id)))
            kingbird_global_limit = self._get_kingbird_project_limit(
                project_id)
            # Get unused quotas
            unused_quota = set(
                kingbird_global_limit).difference(set(total_usage.keys()))
            # Create a dict with value as '0' for unused quotas
            unused_quota = dict((quota_name, 0) for quota_name in unused_quota)
            total_usage.update(unused_quota)
            return {'limits': kingbird_global_limit,
                    'usage': total_usage}
        except exceptions.NotFound:
            raise


def list_opts():
    yield batch_opt_group.name, batch_opts
