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

from kingbird.drivers import base

from neutronclient.neutron import client

LOG = log.getLogger(__name__)
API_VERSION = '2.0'


class NeutronClient(base.DriverBase):
    '''Neutron V2 driver.'''
    def __init__(self, context, region=None, token=None):
        region = region if region else context.region
        self.neutron_client = client.Client(
            API_VERSION, username=context.user_name, password=context.password,
            tenant_name=context.tenant_name, auth_url=context.auth_url,
            region_name=region)

    def get_resource_usages(self, project_id):
        '''Calcualte resources usage and return the dict'''
        return {}

    def update_quota_limits(self, project_id, new_quota):
        '''Update the limits'''
        pass

    def delete_quota_limits(self, project_id):
        '''Delete/Reset the limits'''
        pass
