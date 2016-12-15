# Copyright 2016 Ericsson AB
#
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

from kingbird.engine import resource_manager
from kingbird.tests import base
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = 'fake_target_region'
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class TestResourceManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestResourceManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @mock.patch.object(resource_manager, 'context')
    def test_init(self, mock_context):
        mock_context.get_admin_context.return_value = self.ctxt
        rm = resource_manager.ResourceManager()
        self.assertIsNotNone(rm)
        self.assertEqual('resource_manager', rm.service_name)
        self.assertEqual('localhost', rm.host)
        self.assertEqual(self.ctxt, rm.context)

    @mock.patch.object(resource_manager, 'sdk')
    @mock.patch.object(resource_manager.ResourceManager, 'check_keypair')
    def test_resource_sync_force_false(self, mock_check_keypair,
                                       mock_sdk):
        payload = {}
        payload['resource_type'] = 'keypair'
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        overlapped_resources = {}
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        rm = resource_manager.ResourceManager()
        rm.resource_sync_for_user(payload, FAKE_USER_ID, FAKE_RESOURCE_ID)
        mock_check_keypair.assert_called_once_with(payload['target'][0],
                                                   fake_key, FAKE_USER_ID,
                                                   overlapped_resources)
        mock_sdk.OpenStackDriver().get_keypairs.\
            assert_called_once_with(FAKE_USER_ID, FAKE_RESOURCE_ID)

    @mock.patch.object(resource_manager, 'sdk')
    @mock.patch.object(resource_manager.ResourceManager, 'create_keypair')
    def test_resource_sync_force_true(self, mock_create_keypair,
                                      mock_sdk):
        payload = {}
        payload['resource_type'] = 'keypair'
        payload['target'] = [FAKE_TARGET_REGION]
        sync_regions = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        rm = resource_manager.ResourceManager()
        rm.resource_sync_for_user(payload, FAKE_USER_ID, FAKE_RESOURCE_ID)
        mock_create_keypair.assert_called_once_with(payload['force'],
                                                    sync_regions[0],
                                                    fake_key,
                                                    FAKE_USER_ID)

    @mock.patch.object(resource_manager, 'sdk')
    def test_create_keypair(self, mock_sdk):
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        rm = resource_manager.ResourceManager()
        rm.create_keypair(DEFAULT_FORCE, FAKE_SOURCE_REGION,
                          fake_key, FAKE_USER_ID)
        mock_sdk.OpenStackDriver().create_keypairs.\
            assert_called_once_with(DEFAULT_FORCE, fake_key, FAKE_USER_ID)
