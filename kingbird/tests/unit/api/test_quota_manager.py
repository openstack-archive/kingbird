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

from kingbird.api.controllers import quota_manager
from kingbird.common import config
from kingbird.rpc import client as rpc_client
from kingbird.tests.unit.api.testroot import KBApiTest
config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")


class Result(object):
    def __init__(self, project_id, resource, hard_limit):
        self.project_id = project_id
        self.resource = resource
        self.hard_limit = hard_limit


class TestQuotaManager(KBApiTest):
    def setUp(self):
        super(TestQuotaManager, self).setUp()
        cfg.CONF.set_override('admin_tenant', 'fake_tenant_id',
                              group='cache')

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_admin(self, mock_db_api):
        Res = Result('tenant_1', 'ram', 100)
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set': {'project_id': 'tenant_1', 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_admin(self, mock_db_api):
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/defaults',
            headers={'X_ROLE': 'admin'})
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
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/detail',
            headers={'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_admin(self, mock_db_api):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        response = self.app.put_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({Res.project_id: {Res.resource: Res.hard_limit}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_admin(self, mock_db_api):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        response = self.app.delete_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'Deleted quota limits': [Res.resource]},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_all_admin(self, mock_db_api):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_destroy_all.return_value = Res
        response = self.app.delete_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual('Deleted all quota limits for the given project',
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_admin(self):
        response = self.app.put_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/sync',
            headers={'X-Tenant-Id': 'fake_tenant',
                     'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual("triggered quota sync for tenant_1",
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_put_nonadmin(self):
        Res = Result('tenant_1', 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        try:
            self.app.put_json('/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                              headers={'X-Tenant-Id': 'fake_tenant'},
                              params=data)
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_all_nonadmin(self):
        try:
            self.app.delete_json('/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                                 headers={'X-Tenant-Id': 'fake_tenant'})
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_delete_nonadmin(self):
        Res = Result('tenant_1', 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        try:
            self.app.delete_json('/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                                 headers={'X-Tenant-Id': 'fake_tenant'},
                                 params=data)
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_nonadmin(self):
        try:
            self.app.put_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/sync',
                headers={'X-Tenant-Id': 'fake_tenant'})
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all_nonadmin(self, mock_db_api):
        Res = Result('tenant_1', 'ram', 100)
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X_TENANT_ID': 'fake_tenant', 'X_USER_ID': 'nonadmin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set': {'project_id': 'tenant_1', 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_nonadmin(self, mock_db_api):
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/defaults',
            headers={'X_TENANT_ID': 'fake_tenant', 'X_USER_ID': 'nonadmin'})
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_request(self):
        try:
            self.app.post_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/sync',
                headers={'X-Tenant-Id': 'fake_tenant',
                         'X_ROLE': 'admin'})
        except webtest.app.AppError as bad_method_exception:
            self.assertIn('Bad response: 404 Not Found',
                          bad_method_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_payload(self, mock_db_api):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_update.return_value = Res
        data = {'quota': {Res.resource: Res.hard_limit}}
        try:
            self.app.put_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_payload_exception:
            self.assertIn('400 Bad Request',
                          invalid_payload_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_put_invalid_input(self, mock_db_api):
        Res = Result('tenant_1', 'cores', -10)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        try:
            self.app.put_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_input_exception:
            self.assertIn('400 Bad Request',
                          invalid_input_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_invalid_quota(self, mock_db_api):
        Res = Result('tenant_1', 'invalid_quota', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        try:
            self.app.delete_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
                params=data)
        except webtest.app.AppError as invalid_quota_exception:
            self.assertIn('The resource could not be found',
                          invalid_quota_exception.message)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_usages_nonadmin(self, mock_rpc_client):
        expected_usage = {"ram": 10}
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/detail',
            headers={'X_TENANT_ID': 'fake_tenant', 'X_USER_ID': 'nonadmin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_action(self):
        try:
            self.app.put_json(
                '/v1.0/fake_tenant_id/os-quota-sets/tenant_1/syncing',
                headers={'X-Tenant-Id': 'fake_tenant',
                         'X_ROLE': 'admin'})
        except webtest.app.AppError as bad_method_exception:
            self.assertIn('Invalid action, only sync is allowed',
                          bad_method_exception.message)
