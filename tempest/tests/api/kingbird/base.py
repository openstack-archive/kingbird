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


from tempest.common import kingbird
from tempest import config
from tempest.lib.common import api_version_utils
import tempest.test

CONF = config.CONF


class BaseKingbirdTest(api_version_utils.BaseMicroversionTest,
                       tempest.test.BaseTestCase):
    """Base test case class for all Kingbird API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseKingbirdTest, cls).skip_checks()
        if not CONF.service_available.kingbird:
            raise cls.skipException("Kingbird is not available")
        # import config variables

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseKingbirdTest, cls).setup_credentials()
        cls.auth_token = kingbird.get_keystone_authtoken()

    @classmethod
    def setup_clients(cls):
        super(BaseKingbirdTest, cls).setup_clients()

    @classmethod
    def resource_setup(cls):
        super(BaseKingbirdTest, cls).resource_setup()

    @classmethod
    def resource_cleanup(cls):
        super(BaseKingbirdTest, cls).resource_cleanup()

    def setUp(self):
        super(BaseKingbirdTest, self).setUp()

    @classmethod
    def create_custom_kingbird_quota(cls, project_id, new_quota_values):
        new_values = kingbird.create_custom_kingbird_quota(
            cls.auth_token, project_id, new_quota_values)
        return new_values

    @classmethod
    def get_custom_kingbird_quota(cls, project_id):
        return_quotas = kingbird.get_custom_kingbird_quota(
            cls.auth_token, project_id)
        return return_quotas

    @classmethod
    def delete_custom_kingbird_quota(cls, project_id, quota_to_delete=None):
        deleted_quotas = kingbird.delete_custom_kingbird_quota(
            cls.auth_token, project_id, quota_to_delete)
        return deleted_quotas

    @classmethod
    def get_default_kingbird_quota(cls):
        return_quotas = kingbird.get_default_kingbird_quota(cls.auth_token)
        return return_quotas

    @classmethod
    def quota_sync_for_project(cls, project_id):
        sync_status = kingbird.quota_sync_for_project(
            cls.auth_token, project_id)
        return sync_status

    @classmethod
    def get_quota_usage_for_project(cls, project_id):
        quota_usage = kingbird.get_quota_usage_for_project(
            cls.auth_token, project_id)
        return quota_usage

    @classmethod
    def create_custom_kingbird_quota_wrong_token(cls, project_id,
                                                 new_quota_values):
        new_values = kingbird.create_custom_kingbird_quota_wrong_token(
            cls.auth_token, project_id, new_quota_values)
        return new_values
