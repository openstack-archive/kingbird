# Copyright 2012 OpenStack Foundation
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

import uuid

from tempest.api.kingbird import base
from tempest import config

CONF = config.CONF
FAKE_PROJECT = str(uuid.uuid4())
DEFAULT_QUOTAS = {
    u'quota_set': {
        u'metadata_items': 128, u'subnet': 10, u'consistencygroups': 10,
        u'floatingip': 50, u'gigabytes': 1000, u'backup_gigabytes': 1000,
        u'ram': 51200, u'floating_ips': 10, u'snapshots': 10,
        u'instances': 10, u'key_pairs': 100, u'volumes': 10, u'router': 10,
        u'security_group': 10, u'cores': 20, u'backups': 10, u'fixed_ips': -1,
        u'port': 50, u'security_groups': 10, u'network': 10
        }
    }


class KingbirdTestJSON(base.BaseKingbirdTest):

    @classmethod
    def setup_clients(cls):
        super(KingbirdTestJSON, cls).setup_clients()

    def tearDown(self):
        super(KingbirdTestJSON, self).tearDown()

    def test_kingbird_put_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        actual_value = self.create_custom_kingbird_quota(FAKE_PROJECT,
                                                         new_quota)
        expected_value = {FAKE_PROJECT: new_quota["quota_set"]}
        self.assertEqual(expected_value, eval(actual_value))

    def test_kingbird_get_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(FAKE_PROJECT,
                                          new_quota)
        actual_value = self.get_custom_kingbird_quota(FAKE_PROJECT)
        new_quota["quota_set"].update({'project_id': FAKE_PROJECT})
        self.assertEqual(new_quota, eval(actual_value))

    def test_kingbird_delete_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        quota_to_delete = {"quota_set": ["cores"]}
        self.create_custom_kingbird_quota(FAKE_PROJECT,
                                          new_quota)
        self.delete_custom_kingbird_quota(FAKE_PROJECT,
                                          quota_to_delete)
        quota_after_delete = eval(self.get_custom_kingbird_quota(
            FAKE_PROJECT))
        self.assertNotIn("cores", quota_after_delete["quota_set"])

    def test_kingbird_delete_all_method(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(FAKE_PROJECT,
                                          new_quota)
        self.delete_custom_kingbird_quota(FAKE_PROJECT)
        actual_quota_after_delete = eval(self.get_custom_kingbird_quota(
            FAKE_PROJECT))
        expected_quota_after_delete = {"quota_set":
                                       {"project_id": FAKE_PROJECT}}
        self.assertEqual(expected_quota_after_delete,
                         actual_quota_after_delete)

    def test_kingbird_get_default_method_after_update(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(FAKE_PROJECT,
                                          new_quota)
        actual_value = self.get_default_kingbird_quota()
        self.assertEqual(eval(actual_value), DEFAULT_QUOTAS)
        self.delete_custom_kingbird_quota(FAKE_PROJECT)

    def test_quota_sync_for_project(self):
        actual_value = self.quota_sync_for_project(FAKE_PROJECT)
        expected_value = u'triggered quota sync for ' + FAKE_PROJECT
        self.assertEqual(eval(actual_value), expected_value)

    def test_get_quota_usage_for_project(self):
        actual_usage = self.get_quota_usage_for_project(FAKE_PROJECT)
        expected_usage = {u'quota_set': {u'key_pairs': 1}}
        # Assert nova usage, which will be common for all projects
        self.assertEqual(eval(actual_usage), expected_usage)

    def test_kingbird_put_method_wrong_token(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        response = self.create_custom_kingbird_quota_wrong_token(FAKE_PROJECT,
                                                                 new_quota)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.text, u'Authentication required')

    def test_kingbird_get_default_method_after_delete(self):
        new_quota = {"quota_set": {"instances": 15, "cores": 10}}
        self.create_custom_kingbird_quota(FAKE_PROJECT,
                                          new_quota)
        self.delete_custom_kingbird_quota(FAKE_PROJECT)
        actual_value = self.get_default_kingbird_quota()
        self.assertEqual(eval(actual_value), DEFAULT_QUOTAS)
        self.delete_custom_kingbird_quota(FAKE_PROJECT)
