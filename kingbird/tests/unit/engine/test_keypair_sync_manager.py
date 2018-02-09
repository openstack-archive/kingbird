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

from kingbird.engine import keypair_sync_manager
from kingbird.tests import base
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = 'fake_target_region'
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_JOB_ID = utils.UUID1
FAKE_RESOURCE_SYNC_ID = utils.UUID2


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class TestKeypairSyncManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestKeypairSyncManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @mock.patch.object(keypair_sync_manager, 'NovaClient')
    @mock.patch.object(keypair_sync_manager, 'EndpointCache')
    @mock.patch.object(keypair_sync_manager, 'db_api')
    def test_keypair_sync_force_false(self, mock_db_api,
                                      mock_endpoint_cache, mock_nova):
        resource_job = dict()
        resource_job['id'] = FAKE_JOB_ID
        resource_job['target_region'] = [FAKE_TARGET_REGION]
        resource_job['source_region'] = FAKE_SOURCE_REGION
        resource_job['resource'] = [SOURCE_KEYPAIR]
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_db_api.resource_sync_list.return_value = [resource_job]
        mock_nova().get_keypairs.return_value = fake_key
        ksm = keypair_sync_manager.KeypairSyncManager()
        ksm.resource_sync(self.ctxt, FAKE_JOB_ID, DEFAULT_FORCE,
                          [FAKE_RESOURCE_SYNC_ID])
        mock_db_api.resource_sync_list.assert_called_once_with(
            self.ctxt, FAKE_JOB_ID, FAKE_RESOURCE_SYNC_ID)
        mock_nova().get_keypairs.assert_called_once_with(
            resource_job['resource'])

    @mock.patch.object(keypair_sync_manager, 'NovaClient')
    @mock.patch.object(keypair_sync_manager, 'EndpointCache')
    @mock.patch.object(keypair_sync_manager, 'db_api')
    def test_keypair_sync_force_true(self, mock_db_api, mock_endpoint_cache,
                                     mock_nova):
        resource_job = dict()
        resource_job['id'] = FAKE_JOB_ID
        resource_job['target_region'] = [FAKE_TARGET_REGION]
        resource_job['source_region'] = FAKE_SOURCE_REGION
        resource_job['resource'] = [SOURCE_KEYPAIR]
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_db_api.resource_sync_list.return_value = [resource_job]
        mock_nova().get_keypairs.return_value = fake_key
        ksm = keypair_sync_manager.KeypairSyncManager()
        ksm.resource_sync(self.ctxt, FAKE_JOB_ID, True,
                          [FAKE_RESOURCE_SYNC_ID])
        mock_db_api.resource_sync_list.assert_called_once_with(
            self.ctxt, FAKE_JOB_ID, FAKE_RESOURCE_SYNC_ID)
        mock_nova().get_keypairs.assert_called_once_with(
            resource_job['resource'])

    @mock.patch.object(keypair_sync_manager, 'NovaClient')
    @mock.patch.object(keypair_sync_manager, 'db_api')
    def test_create_keypair(self, mock_db_api, mock_nova):
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        ksm = keypair_sync_manager.KeypairSyncManager()
        ksm.create_resources_in_region(
            FAKE_JOB_ID, DEFAULT_FORCE, FAKE_TARGET_REGION,
            fake_key, 'fake_session', self.ctxt)
        mock_nova().create_keypairs.\
            assert_called_once_with(DEFAULT_FORCE, fake_key)
        self.assertEqual(1, mock_db_api.resource_sync_update.call_count)
