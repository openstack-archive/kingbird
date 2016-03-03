# Copyright 2016 Ericsson AB

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

from oslo_log import log

from kingbird.common import consts
from kingbird.common import exceptions
from kingbird.drivers import base

from novaclient import client

LOG = log.getLogger(__name__)
API_VERSION = '2.1'


class NovaClient(base.DriverBase):
    '''Nova V2.1 driver.'''
    def __init__(self, region, disabled_quotas, session):
        try:
            self.nova_client = client.Client(API_VERSION,
                                             session=session,
                                             region_name=region)
            self.enabled_quotas = list(set(consts.NOVA_QUOTA_FIELDS) -
                                       set(disabled_quotas))
            self.no_neutron = True if 'floatingips' in self.enabled_quotas \
                or 'fixedips' in self.enabled_quotas else False
        except exceptions.ServiceUnavailable:
            raise

    def get_resource_usages(self, project_id):
        """Collects resource usages for a given project

        :params: project_id
        :return: dictionary of corresponding resources with its usage
        """
        try:
            resource_usage = {}
            resource_usage['ram'] = 0
            resource_usage['cores'] = 0
            resource_usage['instances'] = 0
            resource_usage['disks'] = 0
            resource_usage['metadata_items'] = 0
            # If neutron is not enabled, calculate below resources from nova
            if self.no_neutron:
                resource_usage['security_groups'] = \
                    len(self.nova_client.security_groups.list())
                resource_usage['floating_ips'] = 0
                resource_usage['fixed_ips'] = 0

            resource_usage['key_pairs'] = \
                len(self.nova_client.keypairs.list())
            for current_server in self.nova_client.servers.list(
                search_opts={'tenant_id': project_id, 'all_tenants': True}):
                flavor_id = current_server.flavor['id']
                flavor_details = self.nova_client.flavors.get(flavor_id)
                resource_usage['ram'] += flavor_details.ram
                resource_usage['cores'] += flavor_details.vcpus
                resource_usage['disks'] += flavor_details.disk
                resource_usage['instances'] += 1
                resource_usage['metadata_items'] += \
                    len(current_server.metadata)
                if self.no_neutron:
                    address = current_server.addresses
                    for current_address in address:
                        for current_ip in address[current_address]:
                            if current_ip['OS-EXT-IPS:type'] == 'floating':
                                resource_usage['floating_ips'] += 1
                            elif current_ip['OS-EXT-IPS:type'] == 'fixed':
                                resource_usage['fixed_ips'] += 1
            return resource_usage
        except exceptions.InternalError:
            raise

    def update_quota_limits(self, project_id, **new_quota):
        """Updates quota limits for a given project

        :params: project_id, dictionary with the quota limits to update
        :return: Nothing
        """
        try:
            if not self.no_neutron:
                if 'floating_ips' in new_quota:
                    del new_quota['floating_ips']
                if 'fixed_ips' in new_quota:
                    del new_quota['fixed_ips']
                if 'security_groups' in new_quota:
                    del new_quota['security_groups']
            return self.nova_client.quotas.update(project_id,
                                                  **new_quota)
        except exceptions.InternalError:
            raise

    def delete_quota_limits(self, project_id):
        """Delete/Reset quota limits for a given project

        :params: project_id
        :return: Nothing
        """
        try:
            return self.nova_client.quotas.delete(project_id)
        except exceptions.InternalError:
            raise
