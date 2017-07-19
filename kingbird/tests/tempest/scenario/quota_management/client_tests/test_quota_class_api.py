# Copyright 2016 Ericsson AB
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

import kingbirdclient

from kingbird.tests.tempest.scenario.quota_management. \
    client_tests import base
from kingbird.tests import utils

DEFAULT_CLASS = "default"
DEFAULT_QUOTAS = base.DEFAULT_QUOTAS
QUOTA_CLASS_FORMAT = base.DEFAULT_QUOTAS.copy()


class KingbirdQuotaClassTestJSON(base.BaseKingbirdTest):

    @classmethod
    def setup_clients(self):
        super(KingbirdQuotaClassTestJSON, self).setup_clients()

    def tearDown(self):
        super(KingbirdQuotaClassTestJSON, self).tearDown()

    @classmethod
    def resource_cleanup(self):
        super(KingbirdQuotaClassTestJSON, self).resource_cleanup()
        self.delete_resources()

    @classmethod
    def resource_setup(self):
        super(KingbirdQuotaClassTestJSON, self).resource_setup()
        self.create_resources()

    def _delete_quota_values(self, class_name):
        quota_value = self.get_quota_for_class(class_name)
        resource_value = quota_value['cores']
        return resource_value == DEFAULT_QUOTAS['cores']

    def test_kb_quota_class_put_method(self):
        new_quota = {"instances": 15, "cores": 10}
        actual_value = self.update_quota_for_class(
            self.class_name, new_quota)
        expected_value = QUOTA_CLASS_FORMAT
        expected_value['cores'] = 10
        expected_value['instances'] = 15
        expected_value['class_name'] = self.class_name
        self.assertEqual(expected_value, actual_value)
        self.delete_quota_for_class(self.class_name)
        utils.wait_until_true(
            lambda: self._delete_quota_values(self.class_name),
            exception=RuntimeError("Timed out "))

    def test_kb_quota_class_get_method(self):
        new_quota = {"instances": 15, "cores": 10}
        self.update_quota_for_class(self.class_name, new_quota)
        actual_value = self.get_quota_for_class(self.class_name)
        expected_value = QUOTA_CLASS_FORMAT
        expected_value['cores'] = 10
        expected_value['instances'] = 15
        expected_value['class_name'] = self.class_name
        self.assertEqual(expected_value, actual_value)
        self.delete_quota_for_class(self.class_name)
        utils.wait_until_true(
            lambda: self._delete_quota_values(self.class_name),
            exception=RuntimeError("Timed out "))

    def test_kb_quota_class_delete_method(self):
        new_quota = {"instances": 15, "cores": 15}
        self.update_quota_for_class(self.class_name, new_quota)
        self.delete_quota_for_class(self.class_name)
        utils.wait_until_true(
            lambda: self._delete_quota_values(self.class_name),
            exception=RuntimeError("Timed out "))
        quota_after_delete = self.get_quota_for_class(self.class_name)
        self.assertNotEqual(quota_after_delete['cores'], 15)
        self.assertNotEqual(quota_after_delete['instances'], 15)

    def test_kb_quota_class_wrong_input(self):
        new_quota = {"instanc": 15, "cores": 10}
        self.assertRaises(kingbirdclient.exceptions.APIException,
                          self.update_quota_for_class, self.class_name,
                          new_quota)

    def test_kb_quota_default_class_get_method(self):
        actual_value = self.get_quota_for_class(DEFAULT_CLASS)
        expected_value = DEFAULT_QUOTAS
        expected_value['class_name'] = DEFAULT_CLASS
        self.assertEqual(actual_value, expected_value)

    def test_kb_quota_class_get_method_for_random_class_name(self):
        actual_value = self.get_quota_for_class("random_class")
        expected_value = DEFAULT_QUOTAS
        expected_value['class_name'] = "random_class"
        self.assertEqual(actual_value, expected_value)

    def test_delete_quota_for_random_class(self):
        self.assertRaisesRegex(kingbirdclient.exceptions.APIException, "404 *",
                               self.delete_quota_for_class, 'random_class')
