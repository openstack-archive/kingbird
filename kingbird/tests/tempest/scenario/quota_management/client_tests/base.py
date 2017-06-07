# Copyright 2016 Ericsson AB.
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

import collections
import time

from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
import tempest.test

from kingbird.tests.tempest.scenario import consts
from kingbird.tests.tempest.scenario.quota_management \
    import sync_client

CONF = config.CONF
GLOBAL_INSTANCE_LIMIT = 10
GLOBAL_NETWORK_LIMIT = 10
GLOBAL_VOLUME_LIMIT = 10
DEFAULT_QUOTAS = consts.DEFAULT_QUOTAS
# Time to wait for sync to finish
TIME_TO_SYNC = CONF.kingbird.TIME_TO_SYNC


class BaseKingbirdTest(api_version_utils.BaseMicroversionTest,
                       tempest.test.BaseTestCase):
    """Base test case class for all Kingbird API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseKingbirdTest, cls).skip_checks()

    def setUp(self):
        super(BaseKingbirdTest, self).setUp()

    @classmethod
    def setup_credentials(cls):
        super(BaseKingbirdTest, cls).setup_credentials()
        session = sync_client.get_session()
        cls.auth_token = session.get_token()
        cls.keystone_client = sync_client.get_keystone_client(session)
        cls.regions = sync_client.get_regions(cls.keystone_client)

    @classmethod
    def setup_clients(cls):
        super(BaseKingbirdTest, cls).setup_clients()

    @classmethod
    def resource_setup(cls):
        super(BaseKingbirdTest, cls).resource_setup()
        cls.class_name = data_utils.rand_name('kb-class')

    @classmethod
    def create_resources(cls):
        # Create Project, User, flavor, subnet & network for test
        project_name = data_utils.rand_name('kb-project')
        user_name = data_utils.rand_name('kb-user')
        password = data_utils.rand_name('kb-password')
        target_project_name = data_utils.rand_name('kb-target-project')
        target_user_name = data_utils.rand_name('kb-target-user')
        cls.openstack_details = sync_client.get_openstack_drivers(
            cls.keystone_client, cls.regions[0], project_name, user_name,
            password, target_project_name, target_user_name)
        cls.openstack_drivers = cls.openstack_details['os_drivers']
        cls.session = cls.openstack_details['session']
        cls.token = cls.openstack_details['token']
        cls.target_token = cls.openstack_details['target_token']
        cls.resource_ids = sync_client.create_resources(cls.openstack_drivers)
        cls.resource_ids.update(cls.openstack_details)
        cls.resource_ids["server_ids"] = []
        cls.session = cls.openstack_details['session']

    @classmethod
    def resource_cleanup(cls):
        super(BaseKingbirdTest, cls).resource_cleanup()

    @classmethod
    def delete_resources(cls):
        sync_client.resource_cleanup(cls.openstack_drivers, cls.resource_ids)

    @classmethod
    def create_custom_kingbird_quota(cls, project_id, new_quota_values):
        new_values = sync_client.create_custom_kingbird_quota(
            cls.openstack_drivers, project_id, new_quota_values)
        return new_values

    @classmethod
    def get_kingbird_quota_another_tenant(cls, target_project_id):
        new_values = sync_client.get_kingbird_quota_another_tenant(
            cls.openstack_drivers, target_project_id)
        return new_values

    @classmethod
    def get_own_kingbird_quota(cls, target_project_id):
        return_quotas = sync_client.get_own_kingbird_quota(
            cls.target_token, target_project_id)
        return return_quotas

    @classmethod
    def delete_custom_kingbird_quota(cls, target_project_id):
        sync_client.delete_custom_kingbird_quota(
            cls.openstack_drivers, target_project_id)

    @classmethod
    def get_default_kingbird_quota(cls, project_id):
        return_quotas = sync_client.get_default_kingbird_quota(
            cls.target_token, project_id)
        return return_quotas

    @classmethod
    def quota_sync_for_project(cls, project_id):
        sync_status = sync_client.quota_sync_for_project(
            cls.openstack_drivers, project_id)
        return sync_status

    @classmethod
    def get_quota_usage_for_project(cls, project_id):
        quota_usage = sync_client.get_quota_usage_for_project(
            cls.openstack_drivers, project_id)
        return quota_usage

    @classmethod
    def create_custom_kingbird_quota_wrong_token(cls, target_project_id,
                                                 new_quota_values):
        new_values = sync_client.kingbird_create_quota_wrong_token(
            cls.openstack_drivers, target_project_id, new_quota_values)
        return new_values

    @classmethod
    def create_instance(cls, count=1):
        try:
            server_ids = sync_client.create_instance(cls.openstack_drivers,
                                                     cls.resource_ids, count)
        except Exception as e:
            server_ids = list(e.args)
            raise
        finally:
            cls.resource_ids["server_ids"].extend(server_ids)

    @classmethod
    def delete_instance(cls):
        sync_client.delete_instance(cls.openstack_drivers, cls.resource_ids)

    @classmethod
    def calculate_quota_limits(cls, project_id):
        calculated_quota_limits = collections.defaultdict(dict)
        resource_usage = sync_client.get_usage_from_os_client(
            cls.session, cls.regions, project_id)
        total_usages = cls.get_summation(resource_usage)
        for current_region in cls.regions:
            # Calculate new limit for instance count
            global_remaining_limit = GLOBAL_INSTANCE_LIMIT - \
                total_usages['instances']
            instances_limit = global_remaining_limit + resource_usage[
                current_region]['instances']
            # Calculate new limit for network count
            global_remaining_limit = GLOBAL_NETWORK_LIMIT - \
                total_usages['network']
            network_limit = global_remaining_limit + resource_usage[
                current_region]['network']
            # Calculate new limit for volume count
            global_remaining_limit = GLOBAL_VOLUME_LIMIT - \
                total_usages['volumes']
            volume_limit = global_remaining_limit + resource_usage[
                current_region]['volumes']
            calculated_quota_limits.update(
                {current_region: [instances_limit, network_limit,
                                  volume_limit]})
        return calculated_quota_limits

    @classmethod
    def get_summation(cls, regions_dict):
        # Adds resources usages from different regions
        single_region = {}
        resultant_dict = collections.Counter()
        for current_region in regions_dict:
            single_region[current_region] = collections.Counter(
                regions_dict[current_region])
            resultant_dict += single_region[current_region]
        return dict(resultant_dict)

    @classmethod
    def get_usage_manually(cls, project_id):
        resource_usage = sync_client.get_usage_from_os_client(
            cls.session, cls.regions, project_id)
        resource_usage = cls.get_summation(resource_usage)
        return {'quota_set': resource_usage}

    @classmethod
    def get_actual_limits(cls, project_id):
        actual_limits = sync_client.get_actual_limits(
            cls.session, cls.regions, project_id)
        return actual_limits

    @classmethod
    def wait_sometime_for_sync(cls):
        time.sleep(TIME_TO_SYNC)

    @classmethod
    def set_default_quota(cls, project_id, quota_to_set):
        sync_client.set_default_quota(
            cls.session, cls.regions, project_id, **quota_to_set)

    @classmethod
    def update_quota_for_class(cls, class_name, new_quota_values):
        new_values = sync_client.update_quota_for_class(
            cls.openstack_drivers, class_name, new_quota_values)
        return new_values

    @classmethod
    def get_quota_for_class(cls, class_name):
        return_quotas = sync_client.get_quota_for_class(
            cls.openstack_drivers, class_name)
        return return_quotas

    @classmethod
    def delete_quota_for_class(cls, class_name):
        deleted_quotas = sync_client.delete_quota_for_class(
            cls.openstack_drivers, class_name)
        return deleted_quotas
