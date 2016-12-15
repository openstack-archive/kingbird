# Copyright (c) 2016 Ericsson AB
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import webtest


from kingbird.api.controllers import resource_manager
from kingbird.rpc import client as rpc_client
from kingbird.tests.unit.api import testroot

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = ['fake_target_region']
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'
FAKE_RESOURCE_TYPE = 'invalid_choice'
RESOURCE_TYPE = 'keypair'
FAKE_URL = '/v1.0/user123/os-sync/user123'
FAKE_HEADERS = {'X_ROLE': 'admin'}


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class TestResourceManager(testroot.KBApiTest):
    def setUp(self):
        super(TestResourceManager, self).setUp()

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(resource_manager, 'sdk')
    def test_resource_sync(self, mock_sdk):
        data = {"resource_set": {'resource_type': RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": FAKE_TARGET_REGION}}
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        response = self.app.post_json(FAKE_URL,
                                      headers=FAKE_HEADERS,
                                      params=data)
        self.assertEqual(2,
                         mock_sdk.OpenStackDriver().get_keypairs.call_count)
        self.assertEqual(response.status_int, 200)
        self.assertEqual("keypair synced for user user123",
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(resource_manager, 'sdk')
    def test_check_keypair_in_region(self, mock_sdk):
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        rm = resource_manager.ResourceManagerController()
        overlapped_resources = {}
        rm._check_keypair_in_region('fake_target_region', FAKE_USER_ID,
                                    fake_key, overlapped_resources)
        mock_sdk.OpenStackDriver().get_keypairs.assert_called_once_with(
            FAKE_USER_ID, fake_key)


class NegativeTestResourceManager(testroot.KBApiTest):
    def setUp(self):
        super(NegativeTestResourceManager, self).setUp()

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_post_resource_no_body(self):
        data = {}
        self.assertRaisesRegexp(webtest.app.AppError, "400 Bad Request*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_post_resource_no_payload(self):
        data = {"resource_set": {}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 Bad Request*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_post_resource_no_target_region(self):
        data = {"resource_set": {"resource_type": RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": []}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 Bad Request*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_post_resource_no_source_region(self):
        data = {"resource_set": {"resource_type": RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True",
                                 "source": "",
                                 "target": FAKE_TARGET_REGION}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 Bad Request*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(resource_manager, 'sdk')
    def test_post_resource_no_source_keypair(self, mock_sdk):
        data = {"resource_set": {"resource_type": RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True",
                                 "source": "",
                                 "target": FAKE_TARGET_REGION}}
        mock_sdk.OpenStackDriver().get_keypairs.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "404*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_post_resource_no_bad_resource_type(self):
        data = {"resource_set": {"resource_type": FAKE_RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True",
                                 "source": "",
                                 "target": FAKE_TARGET_REGION}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 Bad Request*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(resource_manager, 'sdk')
    def test_resource_sync_with_overlapped_resources_no_force(self, mock_sdk):
        data = {"resource_set": {"resource_type": RESOURCE_TYPE,
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "False",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": FAKE_TARGET_REGION}}
        self.assertRaisesRegexp(webtest.app.AppError, "409 Conflict*",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS,
                                params=data)
