# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''
OpenStack Driver
'''
import collections

from oslo_log import log

from kingbird.drivers.openstack.cinder_v2 import CinderClient
from kingbird.drivers.openstack.keystone_v3 import KeystoneClient
from kingbird.drivers.openstack.neutron_v2 import NeutronClient
from kingbird.drivers.openstack.nova_v2 import NovaClient

LOG = log.getLogger(__name__)


class OpenStackDriver(object):

    os_clients_dict = collections.defaultdict(dict)

    def __init__(self, ctx, region_name=None, token=None):
        # Check if objects are cached and try to use those
        self.region_name = region_name
        if region_name in OpenStackDriver.os_clients_dict:
            self.nova_client = OpenStackDriver.os_clients_dict[
                region_name]['nova']
            self.cinder_client = OpenStackDriver.os_clients_dict[
                region_name]['cinder']
            self.neutron_client = OpenStackDriver.os_clients_dict[
                region_name]['neutron']
        else:
            # Create new objects and cache them
            self.nova_client = NovaClient(ctx, region_name, token)
            self.cinder_client = CinderClient(ctx, region_name, token)
            self.neutron_client = NeutronClient(ctx, region_name, token)
            OpenStackDriver.os_clients_dict[
                region_name] = collections.defaultdict(dict)
            OpenStackDriver.os_clients_dict[region_name][
                'nova'] = self.nova_client
            OpenStackDriver.os_clients_dict[region_name][
                'cinder'] = self.cinder_client
            OpenStackDriver.os_clients_dict[region_name][
                'neutron'] = self.neutron_client
        if 'keystone' in OpenStackDriver.os_clients_dict:
            self.keystone_client = OpenStackDriver.os_clients_dict['keystone']
        else:
            self.keystone_client = KeystoneClient(ctx)
            OpenStackDriver.os_clients_dict['keystone'] = self.keystone_client

    def get_enabled_projects(self):
        try:
            return self.keystone_client.get_enabled_projects()
        # As of now assuming the cached keystone client is out dated
        # and exception is thrown because of it.
        except Exception:
            # Delete the cached object
            del OpenStackDriver.os_clients_dict['keystone']

    def get_resource_usages(self, project_id):
        try:
            nova_usages = self.nova_client.get_resource_usages(project_id)
            neutron_usages = self.neutron_client.get_resource_usages(
                project_id)
            cinder_usages = self.cinder_client.get_resource_usages(project_id)
            return nova_usages, neutron_usages, cinder_usages
        # As of now assuming the cached openstack clients are out dated
        # and exception is thrown because of it.
        except Exception:
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]

    def write_quota_limits(self, project_id, limits_to_write):
        try:
            self.nova_client.update_quota_limits(project_id,
                                                 limits_to_write['nova'])
            self.cinder_client.update_quota_limits(project_id,
                                                   limits_to_write['cinder'])
            self.neutron_client.update_quota_limits(project_id,
                                                    limits_to_write['neutron'])
        # As of now assuming the cached openstack clients are out dated
        # and exception is thrown because of it.
        except Exception:
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]

    def delete_quota_limits(self, project_id):
        try:
            self.nova_client.delete_quota_limits(project_id)
            self.neutron_client.delete_quota_limits(project_id)
            self.cinder_client.delete_quota_limits(project_id)
        # As of now assuming the cached openstack clients are out dated
        # and exception is thrown because of it.
        except Exception:
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]
