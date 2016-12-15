# Copyright (c) 2017 Ericsson AB
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

from oslo_utils import timeutils

from kingbird.api.controllers import sync_manager
from kingbird.rpc import client as rpc_client
from kingbird.tests.unit.api import testroot
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
FAKE_TARGET_REGION = ['fake_target_region']
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'
FAKE_RESOURCE_TYPE = 'keypair'
FAKE_TENANT = utils.UUID1
FAKE_JOB = utils.UUID2
FAKE_URL = '/v1.0/' + FAKE_TENANT + '/os-sync/'
WRONG_URL = '/v1.0/wrong/os-sync/'
fake_user = utils.UUID3
FAKE_STATUS = "IN_PROGRESS"
FAKE_HEADERS = {'X-Tenant-Id': FAKE_TENANT, 'X_ROLE': 'admin'}
NON_ADMIN_HEADERS = {'X-Tenant-Id': FAKE_TENANT}


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class SyncJob(object):
    def __init__(self, id, sync_status, updated_at):
        self.id = id
        self.sync_status = sync_status
        self.updated_at = updated_at


class TestResourceManager(testroot.KBApiTest):
    def setUp(self):
        super(TestResourceManager, self).setUp()
        self.ctx = utils.dummy_context()

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'sdk')
    @mock.patch.object(sync_manager, 'db_api')
    def test_post_keypair_sync(self, mock_db_api, mock_sdk, mock_rpc_client):
        time_now = timeutils.utcnow()
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "resource_type": "keypair",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        sync_job_result = SyncJob(FAKE_JOB, "IN_PROGRESS", time_now)
        mock_sdk.OpenStackDriver().get_keypairs.return_value = fake_key
        mock_db_api.sync_job_create.return_value = sync_job_result
        response = self.app.post_json(FAKE_URL,
                                      headers=FAKE_HEADERS,
                                      params=data)
        self.assertEqual(1,
                         mock_sdk.OpenStackDriver().get_keypairs.call_count)
        self.assertEqual(1,
                         mock_db_api.resource_sync_create.call_count)
        self.assertEqual(1,
                         mock_db_api.sync_job_create.call_count)
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_keypair_sync_wrong_url(self, mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, WRONG_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_no_body(self, mock_rpc_client):
        data = {}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_wrong_payload(self, mock_rpc_client):
        data = {"resources": [SOURCE_KEYPAIR],
                "force": "True", "source": FAKE_SOURCE_REGION,
                "target": [FAKE_TARGET_REGION]}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_no_target_regions(self, mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_no_source_regions(self, mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "force": "True",
                                 "target": [FAKE_TARGET_REGION]}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_no_keys_in_body(self, mock_rpc_client):
        data = {"resource_set": {"force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_no_resource_type(self, mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'sdk')
    def test_post_no_keypairs_in_region(self, mock_sdk, mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "resource_type": "keypair",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        mock_sdk.OpenStackDriver().get_keypairs.return_value = None
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_delete_jobs(self, mock_db_api, mock_rpc_client):
        delete_url = FAKE_URL + '/' + FAKE_JOB
        self.app.delete_json(delete_url, headers=FAKE_HEADERS)
        self.assertEqual(1, mock_db_api.sync_job_delete.call_count)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_wrong_request(self, mock_rpc_client):
        delete_url = WRONG_URL + '/' + FAKE_JOB
        self.assertRaisesRegex(webtest.app.AppError, "400 *",
                               self.app.delete_json, delete_url,
                               headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_invalid_job_id(self, mock_rpc_client):
        delete_url = FAKE_URL + '/fake'
        self.assertRaisesRegex(webtest.app.AppError, "400 *",
                               self.app.delete_json, delete_url,
                               headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_delete_in_progress_job(self, mock_db_api, mock_rpc_client):
        delete_url = FAKE_URL + '/' + FAKE_JOB
        mock_db_api.sync_job_status.return_value = "IN_PROGRESS"
        self.assertRaises(KeyError, self.app.delete_json, delete_url,
                          headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_get_job(self, mock_db_api, mock_rpc_client):
        get_url = FAKE_URL
        self.app.get(get_url, headers=FAKE_HEADERS)
        self.assertEqual(1, mock_db_api.sync_job_list.call_count)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_get_wrong_request(self, mock_db_api, mock_rpc_client):
        get_url = WRONG_URL + '/list'
        self.assertRaisesRegex(webtest.app.AppError, "400 *",
                               self.app.get, get_url,
                               headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_get_wrong_action(self, mock_db_api, mock_rpc_client):
        get_url = FAKE_URL + '/fake'
        self.assertRaises(webtest.app.AppError, self.app.get, get_url,
                          headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_get_active_job(self, mock_db_api, mock_rpc_client):
        get_url = FAKE_URL + '/active'
        self.app.get(get_url, headers=FAKE_HEADERS)
        self.assertEqual(1, mock_db_api.sync_job_list.call_count)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_get_detail_job(self, mock_db_api, mock_rpc_client):
        get_url = FAKE_URL + '/' + FAKE_JOB
        self.app.get(get_url, headers=FAKE_HEADERS)
        self.assertEqual(1, mock_db_api.resource_sync_list_by_job.call_count)
