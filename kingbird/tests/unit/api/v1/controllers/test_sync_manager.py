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

from kingbird.api.controllers.v1 import sync_manager
from kingbird.common import consts
from kingbird.rpc import client as rpc_client
from kingbird.tests.unit.api import test_root_controller as testroot
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'
SOURCE_IMAGE_NAME = 'fake_image'
SOURCE_IMAGE_ID = utils.UUID4
WRONG_SOURCE_IMAGE_ID = utils.UUID5
FAKE_TARGET_REGION = ['fake_target_region']
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = ['fake_id']
FAKE_RESOURCE_TYPE = 'keypair'
FAKE_TENANT = utils.UUID1
FAKE_JOB = utils.UUID2
FAKE_URL = '/v1.0/' + FAKE_TENANT + '/os-sync'
WRONG_URL = '/v1.0/wrong/os-sync'
fake_user = utils.UUID3
FAKE_STATUS = consts.JOB_PROGRESS
FAKE_HEADERS = {'X-Tenant-Id': FAKE_TENANT, 'X_ROLE': 'admin',
                'X-Identity-Status': 'Confirmed'}
NON_ADMIN_HEADERS = {'X-Tenant-Id': FAKE_TENANT}


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class FakeImage(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Result(object):
    def __init__(self, job_id, status, time):
        self.job_id = job_id
        self.status = status
        self.time = time


class SyncJob(object):
    def __init__(self, id, sync_status, created_at):
        self.id = id
        self.sync_status = sync_status
        self.created_at = created_at


class TestResourceManager(testroot.KBApiTest):
    def setUp(self):
        super(TestResourceManager, self).setUp()
        self.ctx = utils.dummy_context()

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'NovaClient')
    @mock.patch.object(sync_manager, 'EndpointCache')
    @mock.patch.object(sync_manager, 'db_api')
    def test_post_keypair_sync(self, mock_db_api, mock_endpoint_cache,
                               mock_nova, mock_rpc_client):
        time_now = timeutils.utcnow()
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "resource_type": "keypair",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        sync_job_result = SyncJob(FAKE_JOB, consts.JOB_PROGRESS, time_now)
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_keypairs.return_value = fake_key
        mock_db_api.sync_job_create.return_value = sync_job_result
        response = self.app.post_json(FAKE_URL,
                                      headers=FAKE_HEADERS,
                                      params=data)
        self.assertEqual(1,
                         mock_nova().get_keypairs.call_count)
        self.assertEqual(1,
                         mock_db_api.resource_sync_create.call_count)
        self.assertEqual(1,
                         mock_db_api.sync_job_create.call_count)
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'GlanceClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_post_image_sync(self, mock_db_api, mock_glance, mock_rpc_client):
        time_now = timeutils.utcnow()
        data = {"resource_set": {"resources": [SOURCE_IMAGE_ID],
                                 "resource_type": "image",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        fake_image = FakeImage(SOURCE_IMAGE_ID, SOURCE_IMAGE_NAME)
        sync_job_result = SyncJob(FAKE_JOB, consts.JOB_PROGRESS, time_now)
        mock_glance().check_image.return_value = fake_image.id
        mock_db_api.sync_job_create.return_value = sync_job_result
        response = self.app.post_json(FAKE_URL,
                                      headers=FAKE_HEADERS,
                                      params=data)
        self.assertEqual(1,
                         mock_glance().check_image.call_count)
        self.assertEqual(1,
                         mock_db_api.resource_sync_create.call_count)
        self.assertEqual(1,
                         mock_db_api.sync_job_create.call_count)
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_post_resource_sync_wrong_url(self, mock_rpc_client):
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
    def test_post_no_resources_in_body(self, mock_rpc_client):
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
    @mock.patch.object(sync_manager, 'EndpointCache')
    @mock.patch.object(sync_manager, 'NovaClient')
    def test_post_no_keypairs_in_region(self, mock_nova, mock_endpoint_cache,
                                        mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_KEYPAIR],
                                 "resource_type": "keypair",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_keypairs.return_value = None
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.post_json, FAKE_URL,
                                headers=FAKE_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'GlanceClient')
    def test_post_no_images_in_source_region(self, mock_glance,
                                             mock_rpc_client):
        data = {"resource_set": {"resources": [SOURCE_IMAGE_ID],
                                 "resource_type": "image",
                                 "force": "True",
                                 "source": FAKE_SOURCE_REGION,
                                 "target": [FAKE_TARGET_REGION]}}
        wrong_image = FakeImage(WRONG_SOURCE_IMAGE_ID, SOURCE_IMAGE_NAME)
        mock_glance().check_image.return_value = wrong_image
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
        mock_db_api.sync_job_status.return_value = consts.JOB_PROGRESS
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

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(sync_manager, 'db_api')
    def test_entries_to_database(self, mock_db_api, mock_rpc_client):
        time_now = timeutils.utcnow()
        result = Result(FAKE_JOB, FAKE_STATUS, time_now)
        mock_db_api.sync_job_create.return_value = result
        sync_manager.ResourceSyncController()._entries_to_database(
            self.ctx, FAKE_TARGET_REGION, FAKE_SOURCE_REGION,
            FAKE_RESOURCE_ID, FAKE_RESOURCE_TYPE, FAKE_JOB)
        mock_db_api.resource_sync_create.assert_called_once_with(
            self.ctx, result, FAKE_TARGET_REGION[0], FAKE_SOURCE_REGION,
            FAKE_RESOURCE_ID[0], FAKE_RESOURCE_TYPE)
