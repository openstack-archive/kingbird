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

DEFAULT_CLASS = "default"


class KingbirdQuotaClassTestJSON(base.BaseKingbirdTest):

    def test_kb_quota_class_put_method(self):
        new_quota = {"quota_class_set": {"instances": 15, "cores": 10}}
        actual_value = self.update_quota_for_class(self.class_name,
                                                   new_quota)
        new_quota["quota_class_set"].update({"id": self.class_name})
        self.assertEqual(new_quota, eval(actual_value))
        self.delete_quota_for_class(self.class_name)

    def test_kb_quota_class_get_method(self):
        new_quota = {"quota_class_set": {"instances": 15, "cores": 10}}
        self.update_quota_for_class(self.class_name,
                                    new_quota)
        actual_value = self.get_quota_for_class(self.class_name)
        new_quota["quota_class_set"].update({'id': self.class_name})
        self.assertEqual(new_quota, eval(actual_value))
        self.delete_quota_for_class(self.class_name)

    def test_kb_quota_class_delete_method(self):
        new_quota = {"quota_class_set": {"instances": 15, "cores": 10}}
        self.update_quota_for_class(self.class_name,
                                    new_quota)
        self.delete_quota_for_class(self.class_name)
        quota_after_delete = eval(self.get_quota_for_class(
            self.class_name))
        self.assertNotIn("cores", quota_after_delete["quota_class_set"])
        self.assertNotIn("instances", quota_after_delete["quota_class_set"])

    def test_kb_quota_class_wrong_input(self):
        new_quota = {"quota_class_unset": {"instances": 15, "cores": 10}}
        actual_value = self.update_quota_for_class(self.class_name,
                                                   new_quota)
        self.assertIn("Missing quota_class_set in the body", actual_value)

    def test_kb_quota_class_wrong_quotas(self):
        new_quota = {"quota_class_set": {"instan": 15, "cor": 10}}
        actual_value = self.update_quota_for_class(self.class_name,
                                                   new_quota)
        self.assertEmpty(actual_value)

    def test_kb_quota_default_class_get_method(self):
        actual_value = self.get_quota_for_class(DEFAULT_CLASS)
        expected_value = {"quota_class_set": base.DEFAULT_QUOTAS["quota_set"]}
        expected_value["quota_class_set"].update({"id": DEFAULT_CLASS})
        self.assertEqual(eval(actual_value), expected_value)

    def test_kb_quota_class_get_method_wrong_class_name(self):
        actual_value = self.get_quota_for_class("no_class")
        expected_value = {"quota_class_set": {"id": "no_class"}}
        self.assertEqual(eval(actual_value), expected_value)
