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
from oslo_utils import uuidutils

from kingbird.api.controllers import quota_manager
from kingbird.common import config
from kingbird.rpc import client as rpc_client
from kingbird.tests.unit.api import testroot
config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")


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
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(fake_tenant, 'ram', 100)
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.get(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set':
                         {'project_id': fake_tenant, 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_admin(self, mock_db_api):
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/defaults'\
            % (fake_tenant)
        response = self.app.get(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'})
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
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.get(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_admin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(target_fake_tenant, 'cores', 10)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.put_json(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({Res.project_id: {Res.resource: Res.hard_limit}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_admin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(target_fake_tenant, 'cores', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.delete_json(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'Deleted quota limits': [Res.resource]},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_all_admin(self, mock_db_api):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_destroy_all.return_value = Res
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.delete_json(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual('Deleted all quota limits for the given project',
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_admin(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/sync'\
            % (fake_tenant, target_fake_tenant)
        response = self.app.put_json(
            fake_url,
            headers={'X-Tenant-Id': fake_tenant,
                     'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual("triggered quota sync for "+target_fake_tenant,
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_put_nonadmin(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result('tenant_1', 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.put_json(fake_url,
                              headers={'X-Tenant-Id': fake_tenant},
                              params=data)
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_all_nonadmin(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.delete_json(fake_url,
                                 headers={'X-Tenant-Id': fake_tenant})
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_nonadmin(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(target_fake_tenant, 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.delete_json(fake_url,
                                 headers={'X-Tenant-Id': fake_tenant},
                                 params=data)
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_nonadmin(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/sync'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.put_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant})
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_nonadmin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/defaults'\
            % (fake_tenant)
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        response = self.app.get(
            fake_url,
            headers={'X_TENANT_ID': fake_tenant, 'X_USER_ID': 'nonadmin'})
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_request(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-ssdfets/%s/sync'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.post_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant,
                         'X_ROLE': 'admin'})
        except webtest.app.AppError as bad_method_exception:
            self.assertIn('Bad response: 404 Not Found',
                          bad_method_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_payload(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(fake_tenant, 'cores', 10)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)

        mock_db_api.quota_update.return_value = Res
        data = {'quota': {Res.resource: Res.hard_limit}}
        try:
            self.app.put_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_payload_exception:
            self.assertIn('400 Bad Request',
                          invalid_payload_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_input(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        Res = Result(fake_tenant, 'cores', -10)
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        try:
            self.app.put_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_input_exception:
            self.assertIn('400 Bad Request',
                          invalid_input_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_invalid_quota(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        Res = Result('tenant_1', 'invalid_quota', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        try:
            self.app.delete_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant, 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_quota_exception:
            self.assertIn('The resource could not be found',
                          invalid_quota_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_action(self):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/syncing'\
            % (fake_tenant, target_fake_tenant)
        try:
            self.app.put_json(
                fake_url,
                headers={'X-Tenant-Id': fake_tenant,
                         'X_ROLE': 'admin'})
        except webtest.app.AppError as bad_method_exception:
            self.assertIn('Invalid action, only sync is allowed',
                          bad_method_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_another_tenant_nonadmin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        FAKE_HEADERS = {'X_TENANT_ID': fake_tenant,
                        'X_USER_ID': 'nonadmin'}
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_another_tenant_with_admin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s'\
            % (fake_tenant, target_fake_tenant)
        Res = Result('tenant_1', 'ram', 100)
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        response = self.app.get(
            fake_url,
            headers={'X_TENANT_ID': fake_tenant, 'X_ROLE': 'admin',
                     'X_USER_ID': 'nonadmin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set': {'project_id': 'tenant_1', 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_usages_another_tenant_no_admin(self, mock_db_api):
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (fake_tenant, target_fake_tenant)
        FAKE_HEADERS = {'X_TENANT_ID': fake_tenant,
                        'X_USER_ID': 'nonadmin'}
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_usages_another_tenant_admin(self, mock_rpc_client):
        expected_usage = {"ram": 10}
        fake_tenant = uuidutils.generate_uuid()
        target_fake_tenant = uuidutils.generate_uuid()
        fake_url = '/v1.0/%s/os-quota-sets/%s/detail'\
            % (fake_tenant, target_fake_tenant)
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        response = self.app.get(
            fake_url,
            headers={'X_TENANT_ID': fake_tenant, 'X_ROLE': 'admin',
                     'X_USER_ID': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/defaults'
        FAKE_HEADERS = {'X_ROLE': 'nonadmin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.get, FAKE_URL,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/defaults'
        FAKE_HEADERS = {'X_ROLE': 'admin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.get, FAKE_URL,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_put_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2/sync'
        FAKE_HEADERS = {'X_ROLE': 'nonadmin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put, FAKE_URL,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_put_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        FAKE_HEADERS = {'X_ROLE': 'admin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put, FAKE_URL,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_invalid_curl_req_nonadmin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        FAKE_HEADERS = {'X_ROLE': 'nonadmin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.delete, FAKE_URL,
                                headers=FAKE_HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_invalid_curl_req_admin(self, mock_rpc_client):
        FAKE_URL = '/v1.0/dummy/os-quota-sets/dummy2'
        FAKE_HEADERS = {'X_ROLE': 'admin'}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.delete, FAKE_URL,
                                headers=FAKE_HEADERS)
