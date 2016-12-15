# Copyright 2017 Ericsson AB
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

from kingbird.engine import sync_manager
from kingbird.tests import base
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = 'fake_target_region'
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'
FAKE_JOB_ID = utils.UUID1


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class TestSyncManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestSyncManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @mock.patch.object(sync_manager, 'context')
    def test_init(self, mock_context):
        mock_context.get_admin_context.return_value = self.ctxt
        sm = sync_manager.SyncManager()
        self.assertIsNotNone(sm)
        self.assertEqual('sync_manager', sm.service_name)
        self.assertEqual('localhost', sm.host)
        self.assertEqual(self.ctxt, sm.context)

    @mock.patch.object(sync_manager, 'sdk')
    @mock.patch.object(sync_manager.SyncManager, '_create_keypairs')
    @mock.patch.object(sync_manager, 'db_api')
    def test_keypair_sync_force_false(self, mock_db_api, mock_create_keypair,
                                      mock_sdk):
        payload = {}
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [SOURCE_KEYPAIR]
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        sm = sync_manager.SyncManager()
        sm.keypair_sync_for_user(FAKE_USER_ID, FAKE_JOB_ID, payload)
        mock_create_keypair.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_key,
            FAKE_USER_ID)

    @mock.patch.object(sync_manager, 'sdk')
    @mock.patch.object(sync_manager.SyncManager, '_create_keypairs')
    @mock.patch.object(sync_manager, 'db_api')
    def test_keypair_sync_force_true(self, mock_db_api, mock_create_keypair,
                                     mock_sdk):

        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [SOURCE_KEYPAIR]
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        sm = sync_manager.SyncManager()
        sm.keypair_sync_for_user(FAKE_USER_ID, FAKE_JOB_ID, payload)
        mock_create_keypair.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], FAKE_TARGET_REGION, fake_key,
            FAKE_USER_ID)

    @mock.patch.object(sync_manager, 'sdk')
    @mock.patch.object(sync_manager, 'db_api')
    def test_create_keypair(self, mock_db_api, mock_sdk):
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        sm = sync_manager.SyncManager()
        sm._create_keypairs(FAKE_JOB_ID, DEFAULT_FORCE, FAKE_TARGET_REGION,
                            fake_key, FAKE_USER_ID)
        mock_sdk.OpenStackDriver().create_keypairs.\
            assert_called_once_with(DEFAULT_FORCE, fake_key, FAKE_USER_ID)
