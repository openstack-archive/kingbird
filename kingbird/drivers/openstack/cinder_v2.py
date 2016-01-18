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

from cinderclient.v2 import client as ci_client

from kingbird.drivers import base

LOG = log.getLogger(__name__)


class CinderClient(base.DriverBase):
    '''Cinder V2 driver.'''
    def __init__(self, region, **kwargs):
        self.cinder_client = ci_client.Client(
            auth_url=kwargs['auth_url'],
            username=kwargs['user_name'],
            api_key=kwargs['password'],
            tenant_id=kwargs['tenant_id'],
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
