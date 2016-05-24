# Copyright (c) 2016 Ericsson AB
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock
import webtest

from oslo_config import cfg

from kingbird.api.controllers.v1 import quota_class
from kingbird.common import config
from kingbird.tests.unit.api.testroot import KBApiTest

config.register_options()
OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")


class Result(object):
    def __init__(self, class_name, resource, hard_limit):
        self.class_name = class_name
        self.resource = resource
        self.hard_limit = hard_limit


class TestQuotaClassController(KBApiTest):
    def setUp(self):
        super(TestQuotaClassController, self).setUp()
        cfg.CONF.set_override('admin_tenant', 'fake_tenant_id',
                              group='cache')

    @mock.patch.object(quota_class, 'db_api')
    def test_get_all_admin(self, mock_db_api):
        result = Result('class1', 'ram', 100)
        mock_db_api.quota_class_get_all_by_name.return_value = \
            {"class_name": result.class_name,
             result.resource: result.hard_limit}
        response = self.app.get(
            '/v1.0/fake_tenant_id/os-quota-class-sets/class1',
            headers={'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_class_set': {'id': 'class1', 'ram': 100}},
                         eval(response.text))

    @mock.patch.object(quota_class, 'db_api')
    def test_put_admin(self, mock_db_api):
        result = Result('class1', 'cores', 10)
        mock_db_api.quota_class_get_all_by_name.return_value = \
            {"class_name": result.class_name,
             result.resource: result.hard_limit}
        data = {"quota_class_set": {result.resource: result.hard_limit}}
        response = self.app.put_json(
            '/v1.0/fake_tenant_id/os-quota-class-sets/class1',
            headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'},
            params=data)
        self.assertEqual(response.status_int, 200)
        self.assertEqual({'quota_class_set': {'id': 'class1', 'cores': 10}},
                         eval(response.text))

    @mock.patch.object(quota_class, 'db_api')
    def test_delete_all_admin(self, mock_db_api):
        result = Result('class1', 'cores', 10)
        mock_db_api.quota_destroy_all.return_value = result
        response = self.app.delete_json(
            '/v1.0/fake_tenant_id/os-quota-class-sets/class1',
            headers={'X-Tenant-Id': 'fake_tenant', 'X_ROLE': 'admin'})
        self.assertEqual(response.status_int, 200)

    def test_delete_all_non_admin(self):
        try:
            self.app.delete_json(
                '/v1.0/fake_tenant_id/os-quota-class-sets/class1',
                headers={'X-Tenant-Id': 'fake_tenant'})
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)

    def test_put_non_admin(self):
        result = Result('class1', 'cores', 10)
        data = {"quota_class_set": {result.resource: result.hard_limit}}
        try:
            self.app.put_json(
                '/v1.0/fake_tenant_id/os-quota-class-sets/class1',
                headers={'X-Tenant-Id': 'fake_tenant'},
                params=data)
        except webtest.app.AppError as admin_exception:
            self.assertIn('Admin required', admin_exception.message)
