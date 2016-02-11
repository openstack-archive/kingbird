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

import mock

import keystoneclient

from kingbird.drivers.openstack import keystone_v3
from kingbird.tests import base
from kingbird.tests import utils

FAKE_ADMIN_CREDS = {
    'user_name': 'fake_user',
    'password': 'pass1234',
    'tenant_name': 'test_tenant',
    'auth_url': 'http://127.0.0.1:5000/v3',
    'project_domain': 'domain1',
    'user_domain': 'user_dom'
    }


class TestKeystoneClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestKeystoneClient, self).setUp()
        self.ctx = utils.dummy_context()

    def test_init(self):
        key_client = keystone_v3.KeystoneClient(**FAKE_ADMIN_CREDS)
        self.assertIsNotNone(key_client.keystone_client)
        self.assertIsInstance(key_client.keystone_client,
                              keystoneclient.v3.client.Client)

    @mock.patch.object(keystone_v3, 'KeystoneClient')
    def test_get_enabled_projects(self, mock_key_client):
        key_client = keystone_v3.KeystoneClient(self.ctx)
        raised = False
        try:
            key_client.get_enabled_projects()
        except Exception:
            raised = True
        self.assertFalse(raised, 'get_enabled_projects Failed')
