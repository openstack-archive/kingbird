# Copyright (c) 2015 Huawei Technologies Co., Ltd.
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

from oslo_config import cfg

from kingbird.api.controllers.v1 import quota_manager
from kingbird.common import config
from kingbird.rpc import client as rpc_client
from kingbird.tests.tempest.scenario import consts as tempest_consts
from kingbird.tests.unit.api import test_root_controller as testroot
from kingbird.tests import utils

config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")
FAKE_TENANT = utils.UUID1
TARGET_FAKE_TENANT = utils.UUID2
ADMIN_HEADERS = {'X-Tenant-Id': FAKE_TENANT, 'X_ROLE': 'admin',
                 'X-Identity-Status': 'Confirmed'}
NON_ADMIN_HEADERS = {'X-Tenant-Id': TARGET_FAKE_TENANT,
                     'X-Identity-Status': 'Confirmed'}


class Result(object):
    def __init__(self, project_id, resource, hard_limit):
        self.project_id = project_id
        self.resource = resource
        self.hard_limit = hard_limit


class TestQuotaManager(testroot.KBApiTest):
    def setUp(self):
        super(TestQuotaManager, self).setUp()
        cfg.CONF.set_override('admin_tenant', 'fake_tenant_id',
                              group='cache')

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_admin(self, mock_db_api):
        updated_values = {'subnet': 11}
        default_values = dict(tempest_consts.DEFAULT_QUOTAS)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, FAKE_TENANT)
        mock_db_api.quota_get_all_by_project.return_value = updated_values
        mock_db_api.quota_class_get_default.return_value = default_values
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        default_values.update(updated_values)
        self.assertEqual(response.json['quota_set'], default_values)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_tenant_with_admin(self, mock_db_api):
        updated_values = {'subnet': 11}
        default_values = dict(tempest_consts.DEFAULT_QUOTAS)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        mock_db_api.quota_get_all_by_project.return_value = updated_values
        mock_db_api.quota_class_get_default.return_value = default_values
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        default_values.update(updated_values)
        self.assertEqual(response.json['quota_set'], default_values)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_tenant_without_admin(self, mock_db_api):
        updated_values = {'subnet': 11}
        default_values = dict(tempest_consts.DEFAULT_QUOTAS)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (TARGET_FAKE_TENANT, TARGET_FAKE_TENANT)
        mock_db_api.quota_get_all_by_project.return_value = updated_values
        mock_db_api.quota_class_get_default.return_value = default_values
        response = self.app.get(
            fake_url,
            headers=NON_ADMIN_HEADERS)
        default_values.update(updated_values)
        self.assertEqual(response.json['quota_set'], default_values)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_admin(self, mock_db_api):
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        fake_url = '/v1.0/%s/os-quota-sets/defaults'\
            % (FAKE_TENANT)
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_usages_admin(self, mock_rpc_client):
        expected_usage = {"ram": 10}
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_admin(self, mock_db_api):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        response = self.app.put_json(
            fake_url,
            headers=ADMIN_HEADERS,
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({Res.project_id: {Res.resource: Res.hard_limit}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_admin(self, mock_db_api):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        response = self.app.delete_json(
            fake_url,
            headers=ADMIN_HEADERS,
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'Deleted quota limits': [Res.resource]},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_all_admin(self, mock_db_api):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        mock_db_api.quota_destroy_all.return_value = Res
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        response = self.app.delete_json(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual('Deleted all quota limits for the given project',
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_admin(self):
        fake_url = '/v1.0/%s/os-quota-sets/%s/sync'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        response = self.app.put_json(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual("triggered quota sync for " + TARGET_FAKE_TENANT,
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_put_nonadmin(self):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.put_json, fake_url,
                                headers=NON_ADMIN_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_all_nonadmin(self):
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.delete_json, fake_url,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_nonadmin(self):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.delete_json, fake_url,
                                headers=NON_ADMIN_HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_nonadmin(self):
        fake_url = '/v1.0/%s/os-quota-sets/%s/sync'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.put_json, fake_url,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_nonadmin(self, mock_db_api):
        fake_url = '/v1.0/%s/os-quota-sets/defaults'\
            % (FAKE_TENANT)
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_request(self):
        fake_url = '/v1.0/%s/os-quota-ssdfets/%s/sync'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.post_json, fake_url,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_payload(self, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', 10)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        mock_db_api.quota_update.return_value = Res
        data = {'quota': {Res.resource: Res.hard_limit}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put_json, fake_url,
                                headers=ADMIN_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_input(self, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', -10)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put_json, fake_url,
                                headers=ADMIN_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_invalid_quota(self, mock_db_api):
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        Res = Result('tenant_1', 'invalid_quota', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.delete_json, fake_url,
                                headers=ADMIN_HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_action(self):
        fake_url = '/v1.0/%s/os-quota-sets/%s/syncing'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.delete_json, fake_url,
                                headers=ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_another_tenant_nonadmin(self, mock_db_api):
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_usages_another_tenant_no_admin(self, mock_db_api):
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (TARGET_FAKE_TENANT, FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_usages_another_tenant_admin(self, mock_rpc_client):
        expected_usage = {"ram": 10}
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (FAKE_TENANT, TARGET_FAKE_TENANT)
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        response = self.app.get(
            fake_url,
            headers=ADMIN_HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/defaults'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.get, FAKE_URL,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/defaults'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.get, FAKE_URL,
                                headers=ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_put_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2/sync'
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.put, FAKE_URL,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_put_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put, FAKE_URL,
                                headers=ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.delete, FAKE_URL,
                                headers=NON_ADMIN_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.delete, FAKE_URL,
                                headers=NON_ADMIN_HEADERS)
