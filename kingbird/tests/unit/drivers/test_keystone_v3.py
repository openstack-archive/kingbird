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
from kingbird.tests import base
from kingbird.tests import utils

FAKE_SERVICE = [
    'endpoint_volume',
    'endpoint_network'
    ]


class TestKeystoneClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestKeystoneClient, self).setUp()
        self.ctx = utils.dummy_context()

    @mock.patch.object(keystone_v3, 'KeystoneClient')
    @mock.patch.object(keystone_v3, 'EndpointCache')
    def test_init(self, mock_endpoint_cache, mock_keystone):
        mock_keystone().services_list = FAKE_SERVICE
        mock_endpoint_cache().admin_session = 'fake_session'
        mock_endpoint_cache().keystone_client = 'fake_key_client'
        key_client = keystone_v3.KeystoneClient()
        self.assertIsNotNone(key_client.keystone_client)
        self.assertEqual(key_client.services_list,
                         FAKE_SERVICE)

    @mock.patch.object(keystone_v3, 'KeystoneClient')
    def test_get_enabled_projects(self, mock_key_client):
        key_client = keystone_v3.KeystoneClient()
        raised = False
        try:
            key_client.get_enabled_projects()
        except Exception:
            raised = True
        self.assertFalse(raised, 'get_enabled_projects Failed')

    @mock.patch.object(keystone_v3, 'KeystoneClient')
    def test_is_service_enabled(self, mock_keystone):
        key_client = keystone_v3.KeystoneClient()
        mock_keystone().is_service_enabled.return_value = True
        network_enabled = key_client.is_service_enabled('network')
        self.assertEqual(network_enabled, True)
