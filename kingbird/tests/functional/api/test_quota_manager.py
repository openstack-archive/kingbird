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

from oslo_config import cfg

from kingbird.api.controllers import quota_manager
from kingbird.common import config
from kingbird.common import exceptions
from kingbird.common import rpc
from kingbird.tests.functional.api.testroot import KBFunctionalTest
config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")


class Result(object):
    def __init__(self, project_id, resource, hard_limit):
        self.project_id = project_id
        self.resource = resource
        self.hard_limit = hard_limit


class TestQuotaManager(KBFunctionalTest):
    def setUp(self):
        super(TestQuotaManager, self).setUp()
        cfg.CONF.set_override('admin_tenant_id', 'fake_tenant_id',
                              group='cache')

    @mock.patch.object(rpc, 'get_client', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_all(self, mock_db_api):
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

    @mock.patch.object(rpc, 'get_client')
    def test_get_default(self, mock_client):
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-sets/defaults',
            headers={'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(quota_manager, 'db_api')
    def test_post(self, mock_db_api, mock_client):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_create.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        response = self.app.post_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'tenid'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({"tenant_1": {"cores": 10}},
                         eval(response.text))

    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(quota_manager, 'db_api')
    def test_put(self, mock_db_api, mock_client):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        response = self.app.put_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'tenid'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({Res.project_id: {Res.resource: Res.hard_limit}},
                         eval(response.text))

    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete(self, mock_db_api, mock_client):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_destroy.return_value = Res
        data = {"quota_set": [Res.resource]}
        response = self.app.delete_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'tenid'},
            params=data)
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(quota_manager, 'db_api')
    def test_delete_all(self, mock_db_api, mock_client):
        Res = Result('tenant_1', 'cores', 10)
        mock_db_api.quota_destroy_all.return_value = Res
        response = self.app.delete_json(
            '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
            headers={'X-Tenant-Id': 'tenid'})
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc, 'get_client')
    def test_quota_sync(self, mock_client):
        response = self.app.post_json('/v1.0/os-quota-sets/sync/tenant_1',
                                      headers={'X-Tenant-Id': 'tenid'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual('"trigered quota sync for tenant_1"',
                         response.text)

    @mock.patch.object(rpc, 'get_client')
    def test_admin_exception(self, mock_client):
        Res = Result('tenant_1', 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        self.assertRaises(exceptions.AdminRequired,
                          self.app.put_json,
                          '/v1.0/fake_tenant_id/os-quota-sets/tenant_1',
                          headers={'X-Tenant-Id': 'tenid'},
                          params=data)
