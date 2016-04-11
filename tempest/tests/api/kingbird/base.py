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
import collections
import time

from tempest.common import kingbird
from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
import tempest.test

CONF = config.CONF
Global_instance_limit = 10
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
# Time to wait for sync to finish
TIME_TO_SYNC = 30


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
        super(BaseKingbirdTest, cls).setup_credentials()
        session = kingbird.get_session()
        cls.auth_token = session.get_token()
        cls.key_client = kingbird.get_key_client(session)
        cls.regions = kingbird.get_regions(cls.key_client)

    @classmethod
    def setup_clients(cls):
        super(BaseKingbirdTest, cls).setup_clients()

    @classmethod
    def resource_setup(cls):
        super(BaseKingbirdTest, cls).resource_setup()
        # Create Project, User, flavor, subnet & network for test
        project_name = data_utils.rand_name(__name__ + '-project')
        user_name = data_utils.rand_name(__name__ + '-user')
        password = data_utils.rand_name(__name__ + '-password')
        openstack_details = kingbird.get_openstack_drivers(cls.key_client,
                                                           cls.regions[0],
                                                           project_name,
                                                           user_name,
                                                           password)
        cls.openstack_drivers = openstack_details['os_drivers']
        cls.resource_ids = kingbird.create_resources(cls.openstack_drivers)
        cls.resource_ids.update(openstack_details)
        cls.session = openstack_details['session']

    @classmethod
    def resource_cleanup(cls):
        super(BaseKingbirdTest, cls).resource_cleanup()
        default_quota = {'instances': DEFAULT_QUOTAS['quota_set']['instances'],
                         'cores': DEFAULT_QUOTAS['quota_set']['cores'],
                         'ram': DEFAULT_QUOTAS['quota_set']['ram']}
        cls.set_default_quota(CONF.kingbird.project_id, default_quota)
        kingbird.resource_cleanup(cls.openstack_drivers, cls.resource_ids)
        kingbird.delete_custom_kingbird_quota(
            cls.auth_token, CONF.kingbird.project_id, None)

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

    @classmethod
    def create_instance(cls, count=1):
        try:
            server_ids = kingbird.create_instance(cls.openstack_drivers,
                                                  cls.resource_ids, count)
        except Exception as e:
            server_ids = {'server_ids': list(e.args)}
            raise
        finally:
            cls.resource_ids.update(server_ids)

    @classmethod
    def delete_instance(cls):
        kingbird.delete_instance(cls.openstack_drivers, cls.resource_ids)
        cls.resource_ids['instances'] = None

    @classmethod
    def calculate_quota_limits(cls, project_id):
        calculated_quota_limits = collections.defaultdict(dict)
        resource_usage = kingbird.get_usage_from_os_client(
            cls.session, cls.regions, project_id)
        total_usages = cls.get_summation(resource_usage)
        for current_region in cls.regions:
            global_remaining_limit = Global_instance_limit - \
                total_usages['instances']
            new_limit_for_region = global_remaining_limit + resource_usage[
                current_region]['instances']
            calculated_quota_limits.update(
                {current_region: new_limit_for_region})
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
        resource_usage = kingbird.get_usage_from_os_client(
            cls.session, cls.regions, project_id)
        resource_usage = cls.get_summation(resource_usage)
        return {'quota_set': resource_usage}

    @classmethod
    def get_actual_limits(cls, project_id):
        actual_limits = kingbird.get_actual_limits(
            cls.session, cls.regions, project_id)
        return actual_limits

    @classmethod
    def wait_sometime_for_sync(cls):
        time.sleep(TIME_TO_SYNC)

    @classmethod
    def set_default_quota(cls, project_id, quota_to_set):
        kingbird.set_default_quota(
            cls.session, cls.regions, project_id, **quota_to_set)
