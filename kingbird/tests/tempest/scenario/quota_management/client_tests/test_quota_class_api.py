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

from kingbird.tests.tempest.scenario.quota_management. \
    client_tests import base

import kingbirdclient

DEFAULT_CLASS = "default"


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

    def test_kb_quota_class_put_method(self):
        expected_quota = {"instances": 15, "cores": 10}
        actual_value = self.update_quota_for_class(self.class_name,
                                                   expected_quota)
        expected_quota.update({"id": self.class_name})
        self.assertEqual(expected_quota, actual_value)
        self.delete_quota_for_class(self.class_name)

    def test_kb_quota_class_get_method(self):
        new_quota = {"instances": 15, "cores": 10}
        self.update_quota_for_class(self.class_name, new_quota)
        actual_value = self.get_quota_for_class(self.class_name)
        new_quota.update({'id': self.class_name})
        self.assertEqual(new_quota, actual_value)
        self.delete_quota_for_class(self.class_name)

    def test_kb_quota_class_delete_method(self):
        new_quota = {"instances": 15, "cores": 10}
        self.update_quota_for_class(self.class_name, new_quota)
        self.delete_quota_for_class(self.class_name)
        quota_after_delete = self.get_quota_for_class(self.class_name)
        self.assertNotIn("cores", quota_after_delete)
        self.assertNotIn("instances", quota_after_delete)

    def test_kb_quota_class_wrong_quotas(self):
        new_quota = {"wrong_input1": 15, "wrong_input2": 10}
        self.assertRaises(kingbirdclient.exceptions.APIException,
                          self.update_quota_for_class,
                          self.class_name, new_quota)

    def test_kb_quota_default_class_get_method(self):
        actual_value = self.get_quota_for_class(DEFAULT_CLASS)
        expected_value = base.DEFAULT_QUOTAS
        expected_value.update({"id": DEFAULT_CLASS})
        self.assertEqual(actual_value, expected_value)

    def test_kb_quota_class_get_method_wrong_class_name(self):
        new_quota = dict()
        actual_value = self.get_quota_for_class('no_class')
        new_quota.update({'id': 'no_class'})
        self.assertEqual(new_quota, actual_value)
        self.delete_quota_for_class(self.class_name)
