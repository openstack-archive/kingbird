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

import mock

from kingbird.drivers.openstack import keystone_v3
from kingbird.drivers.openstack import sdk
from kingbird.tests import base


class TestKeystoneClient(base.KingbirdTestCase):

    @mock.patch.object(sdk.OpenStackDriver, '_create_connection')
    def setUp(self, mock_os_client):
        super(TestKeystoneClient, self).setUp()
        self.keystone_client = mock_os_client.return_value.identity

    def test_init(self):
        keystone_client = keystone_v3.KeystoneClient(self.keystone_client)
        self.assertIsNotNone(keystone_client)

    def test_get_enabled_projects(self):
        keystone_client = keystone_v3.KeystoneClient(self.keystone_client)
        raised = False
        try:
            self.keystone_client.get_enabled_projects()
        except Exception as ex:
            raised = True
        self.assertFalse(raised, 'get_enabled_projects Failed')

    def test_get_regions(self):
        keystone_client = keystone_v3.KeystoneClient(self.keystone_client)
        raised = False
        try:
            keystone_client.get_regions()
        except Exception as ex:
            raised = True
        self.assertFalse(raised, 'get_regions Failed')
