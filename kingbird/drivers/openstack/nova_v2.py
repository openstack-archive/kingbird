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
        except exceptions.ServiceUnavailable:
            raise

    def get_resource_usages(self, project_id):
        '''Calcualte resources usage and return the dict'''
        return {}

    def update_quota_limits(self, project_id, new_quota):
        '''Update the limits'''
        pass

    def delete_quota_limits(self, project_id):
        '''Delete/Reset the limits'''
        pass
