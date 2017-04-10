# Copyright (c) 2017 Ericsson AB.
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
from kingbird.tests.unit.api import test_root_controller as testroot
from kingbird.tests import utils

config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")
TARGET_FAKE_TENANT = utils.UUID1
FAKE_TENANT = utils.UUID2
HEADERS = {'X-Tenant-Id': TARGET_FAKE_TENANT,
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
    @mock.patch.object(quota_manager, 'enf')
    def test_get_quota_details_admin(self, mock_enf, mock_db_api):
        Res = Result(TARGET_FAKE_TENANT, 'ram', 100)
        mock_enf.enforce.return_value = True
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (FAKE_TENANT)
        response = self.app.get(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set':
                         {'project_id': TARGET_FAKE_TENANT, 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    def test_get_default_limits(self, mock_db_api):
        mock_db_api.quota_class_get_default.return_value = \
            {'class_name': 'default'}
        fake_url = '/v1.1/%s/os-quota-sets/defaults'\
            % (TARGET_FAKE_TENANT)
        response = self.app.get(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        result = eval(response.text)
        for resource in result['quota_set']:
            self.assertEqual(
                cfg.CONF.kingbird_global_limit['quota_' + resource],
                result['quota_set'][resource])

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(quota_manager, 'enf')
    def test_get_another_tenant_quota_usages_admin(self, mock_enf,
                                                   mock_rpc_client):
        expected_usage = {"ram": 10}
        mock_enf.enforce.return_value = True
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        fake_url = '/v1.1/%s/os-quota-sets/detail'\
            % (FAKE_TENANT)
        response = self.app.get(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_update_quota_admin(self, mock_enf, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', 10)
        mock_enf.enforce.return_value = True
        mock_db_api.quota_update.return_value = Res
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (FAKE_TENANT)
        response = self.app.put_json(
            fake_url,
            headers=HEADERS,
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({Res.project_id: {Res.resource: Res.hard_limit}},
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_delete_quota_resources_admin(self, mock_enf, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', 10)
        mock_enf.enforce.return_value = True
        mock_db_api.quota_destroy.return_value = Res
        fake_url = '/v1.1/%s/os-quota-sets/?cores'\
            % (FAKE_TENANT)
        response = self.app.delete_json(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_delete_complete_quota_admin(self, mock_enf, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', 10)
        mock_enf.enforce.return_value = True
        mock_db_api.quota_destroy_all.return_value = Res
        fake_url = '/v1.1/%s/os-quota-sets'\
            % (FAKE_TENANT)
        response = self.app.delete_json(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual('Deleted all quota limits for the given project',
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_quota_sync_admin(self, mock_enf):
        fake_url = '/v1.1/%s/os-quota-sets/sync'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = True
        response = self.app.put_json(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual("triggered quota sync for " + FAKE_TENANT,
                         eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_update_nonadmin(self, mock_enf):
        Res = Result(TARGET_FAKE_TENANT, 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.put_json, fake_url,
                                headers=HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_delete_complete_quota_nonadmin(self, mock_enf):
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.delete_json, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_delete_nonadmin(self, mock_enf):
        Res = Result(FAKE_TENANT, 'cores', 10)
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.delete_json, fake_url,
                                headers=HEADERS,
                                params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_quota_sync_nonadmin(self, mock_enf):
        fake_url = '/v1.1/%s/os-quota-sets/sync'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.put_json, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_request(self):
        fake_url = '/v1.1/%s/os-quota-ssdfets/sync'\
            % (FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.post_json, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_update_invalid_payload(self, mock_enf, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', 10)
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (TARGET_FAKE_TENANT)
        mock_db_api.quota_update.return_value = Res
        mock_enf.enforce.return_value = True
        data = {'quota': {Res.resource: Res.hard_limit}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put_json, fake_url,
                                headers=HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_update_invalid_input(self, mock_enf, mock_db_api):
        Res = Result(FAKE_TENANT, 'cores', -10)
        fake_url = '/v1.1/%s/os-quota-sets/'\
            % (TARGET_FAKE_TENANT)
        mock_db_api.quota_update.return_value = Res
        mock_enf.enforce.return_value = True
        data = {"quota_set": {Res.resource: Res.hard_limit}}
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put_json, fake_url,
                                headers=HEADERS, params=data)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    def test_quota_sync_bad_action(self):
        fake_url = '/v1.1/%s/os-quota-sets/syncing'\
            % (TARGET_FAKE_TENANT)
        self.assertRaisesRegexp(webtest.app.AppError, "404 *",
                                self.app.delete_json, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_get_another_tenant_quota_nonadmin(self, mock_enf):
        fake_url = '/v1.1/%s/os-quota-sets'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'enf')
    def test_get_complete_quota_another_tenant_with_admin(self, mock_enf,
                                                          mock_db_api):
        fake_url = '/v1.1/%s/os-quota-sets'\
            % (FAKE_TENANT)
        Res = Result(FAKE_TENANT, 'ram', 100)
        mock_db_api.quota_get_all_by_project.return_value = \
            {"project_id": Res.project_id,
             Res.resource: Res.hard_limit}
        mock_enf.enforce.return_value = True
        response = self.app.get(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_set': {'project_id': FAKE_TENANT,
                          'ram': 100}}, eval(response.text))

    @mock.patch.object(rpc_client, 'EngineClient', new=mock.Mock())
    @mock.patch.object(quota_manager, 'enf')
    def test_get_usages_another_tenant_non_admin(self, mock_enf):
        fake_url = '/v1.1/%s/os-quota-sets/detail'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = False
        self.assertRaisesRegexp(webtest.app.AppError, "403 *",
                                self.app.get, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    @mock.patch.object(quota_manager, 'enf')
    def test_get_usages_another_tenant_admin(self, mock_enf, mock_rpc_client):
        expected_usage = {"ram": 10}
        fake_url = '/v1.1/%s/os-quota-sets/detail'\
            % (FAKE_TENANT)
        mock_enf.enforce.return_value = True
        mock_rpc_client().get_total_usage_for_tenant.return_value = \
            expected_usage
        response = self.app.get(
            fake_url,
            headers=HEADERS)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(eval(response.body), {"quota_set": expected_usage})

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_get_with_invalid_curl_req(self, mock_rpc_client):
        fake_url = '/v1.1/dummy/os-quota-sets/defaults'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.get, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_put_with_invalid_curl_req(self, mock_rpc_client):
        fake_url = '/v1.1/dummy/os-quota-sets'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.put, fake_url,
                                headers=HEADERS)

    @mock.patch.object(rpc_client, 'EngineClient')
    def test_delete_with_invalid_curl_req(self, mock_rpc_client):
        fake_url = '/v1.1/dummy/os-quota-sets'
        self.assertRaisesRegexp(webtest.app.AppError, "400 *",
                                self.app.delete, fake_url,
                                headers=HEADERS)
