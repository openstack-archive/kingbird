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

from tempest import config
from tempest.services.kingbird import base

import novaclient

CONF = config.CONF
DEFAULT_QUOTAS = base.DEFAULT_QUOTAS


class KingbirdTestJSON(base.BaseKingbirdTest):

    @classmethod
    def setup_clients(self):
        super(KingbirdTestJSON, self).setup_clients()

    def tearDown(self):
        super(KingbirdTestJSON, self).tearDown()

    @classmethod
    def resource_setup(self):
        super(KingbirdTestJSON, self).resource_setup()
        self.PROJECT_ID = self.resource_ids["project_id"]

    def test_kingbird_put_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        actual_value = self.create_custom_kingbird_quota(self.PROJECT_ID,
                                                         new_quota)
        expected_value = {self.PROJECT_ID: new_quota["quota_set"]}
        self.assertEqual(expected_value, eval(actual_value))

    def test_kingbird_get_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        actual_value = self.get_custom_kingbird_quota(self.PROJECT_ID)
        new_quota["quota_set"].update({'project_id': self.PROJECT_ID})
        self.assertEqual(new_quota, eval(actual_value))

    def test_kingbird_delete_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        quota_to_delete = {"quota_set": ["cores"]}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        self.delete_custom_kingbird_quota(self.PROJECT_ID,
                                          quota_to_delete)
        quota_after_delete = eval(self.get_custom_kingbird_quota(
            self.PROJECT_ID))
        self.assertNotIn("cores", quota_after_delete["quota_set"])

    def test_kingbird_delete_all_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        self.delete_custom_kingbird_quota(self.PROJECT_ID)
        actual_quota_after_delete = eval(self.get_custom_kingbird_quota(
            self.PROJECT_ID))
        expected_quota_after_delete = {"quota_set":
                                       {"project_id": self.PROJECT_ID}}
        self.assertEqual(expected_quota_after_delete,
                         actual_quota_after_delete)

    def test_kingbird_get_default_method_after_update(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        actual_value = self.get_default_kingbird_quota()
        self.assertEqual(eval(actual_value), DEFAULT_QUOTAS)
        self.delete_custom_kingbird_quota(self.PROJECT_ID)

    def test_get_quota_usage_for_project(self):
        self.create_instance(count=1)
        actual_usage = self.get_quota_usage_for_project(self.PROJECT_ID)
        expected_usage = self.get_usage_manually(self.PROJECT_ID)
        self.assertEqual(eval(actual_usage)["quota_set"]["ram"],
                         expected_usage["quota_set"]["ram"])
        self.assertEqual(eval(actual_usage)["quota_set"]["cores"],
                         expected_usage["quota_set"]["cores"])
        self.assertEqual(eval(actual_usage)["quota_set"]["instances"],
                         expected_usage["quota_set"]["instances"])
        self.delete_instance()

    def test_kingbird_put_method_wrong_token(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        response = self.create_custom_kingbird_quota_wrong_token(
            self.PROJECT_ID, new_quota)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.text, u'Authentication required')

    def test_kingbird_get_default_method_after_delete(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        self.delete_custom_kingbird_quota(self.PROJECT_ID)
        actual_value = self.get_default_kingbird_quota()
        self.assertEqual(eval(actual_value), DEFAULT_QUOTAS)
        self.delete_custom_kingbird_quota(self.PROJECT_ID)

    def test_quota_sync_for_project(self):
        # Delete custom quota if there are any for this project
        self.delete_custom_kingbird_quota(self.PROJECT_ID)
        self.create_instance()
        sync_status = self.quota_sync_for_project(self.PROJECT_ID)
        expected_status = u"triggered quota sync for " + self.PROJECT_ID
        calculated_limits = self.calculate_quota_limits(self.PROJECT_ID)
        self.wait_sometime_for_sync()
        actual_limits = self.get_actual_limits(self.PROJECT_ID)
        self.assertEqual(calculated_limits, actual_limits)
        self.assertEqual(eval(sync_status), expected_status)
        self.delete_instance()

    def test_quota_exceed_after_sync(self):
        new_quota = {"quota_set": {"instances": 2}}
        self.create_custom_kingbird_quota(self.PROJECT_ID,
                                          new_quota)
        self.quota_sync_for_project(self.PROJECT_ID)
        self.wait_sometime_for_sync()
        try:
            self.create_instance(count=3)
        except Exception as exp:
            self.assertIsInstance(exp, novaclient.exceptions.Forbidden)
            message = exp.message
        self.assertIn(u"Quota exceeded for instances", message)
        self.delete_instance()
        default_quota = {'instances': DEFAULT_QUOTAS['quota_set']['instances'],
                         'cores': DEFAULT_QUOTAS['quota_set']['cores'],
                         'ram': DEFAULT_QUOTAS['quota_set']['ram']}
        self.set_default_quota(self.PROJECT_ID, default_quota)
