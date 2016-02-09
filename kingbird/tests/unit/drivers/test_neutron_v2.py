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

from kingbird.drivers.openstack import neutron_v2
from kingbird.tests import base
from kingbird.tests import utils

FAKE_ADMIN_CREDS = {
    'user_name': 'fake_user',
    'password': 'pass1234',
    'tenant_name': 'test_tenant',
    'auth_url': 'http://127.0.0.1:5000/v3'
    }

FAKE_EXTENSIONS = {
    'extensions': ['fake_extension1',
                   'fake_extension2']
    }


class TestNeutronClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestNeutronClient, self).setUp()
        self.ctx = utils.dummy_context()

    @mock.patch.object(neutron_v2, 'NeutronClient')
    def test_init(self, mock_neutron):
        mock_neutron().extension_list = FAKE_EXTENSIONS
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  **FAKE_ADMIN_CREDS)
        self.assertEqual(FAKE_EXTENSIONS,
                         neutron_client.extension_list)

    @mock.patch.object(neutron_v2, 'NeutronClient')
    def test_is_extension_supported(self, mock_neutron):
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  **FAKE_ADMIN_CREDS)
        mock_neutron().is_extension_supported.return_value = True
        extension_enabled = neutron_client.is_extension_supported('quotas')
        self.assertEqual(extension_enabled, True)

    def test_get_resource_usages(self):
        pass

    def test_update_quota_limits(self):
        pass

    def test_delete_quota_limits(self):
        pass
