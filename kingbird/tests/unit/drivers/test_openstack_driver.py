# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock

from oslo_utils import timeutils

from kingbird.drivers.openstack import sdk
from kingbird.tests import base
from kingbird.tests import utils

FAKE_USER_ID = 'user123'
FAKE_RESOURCE_ID = 'fake_id'
DEFAULT_FORCE = False
SOURCE_KEYPAIR = 'fake_key1'


class FakeService(object):

    '''Fake service class used to test service enable testcase

    '''

    def __init__(self, type_service, name):
        self.type = type_service
        self.name = name


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class User(object):
    def __init__(self, user_name, id, enabled=True):
        self.user_name = user_name
        self.id = id
        self.enabled = enabled


class TestOpenStackDriver(base.KingbirdTestCase):
    def setUp(self):
        super(TestOpenStackDriver, self).setUp()

        self.context = utils.dummy_context()
        self.nova_client = None
        self.cinder_client = None
        self.neutron_client = None
        self.keystone_client = None

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_init(self, mock_keystone_client, mock_cinder_client,
                  mock_neutron_client, mock_nova_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        os_driver = sdk.OpenStackDriver('fake_region_1')
        self.assertIsNotNone(os_driver.neutron_client)
        self.assertIsNotNone(os_driver.nova_client)
        self.assertIsNotNone(os_driver.keystone_client)
        self.assertIsNotNone(os_driver.cinder_client)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_get_resource_usages(self, mock_keystone_client,
                                 mock_cinder_client, mock_neutron_client,
                                 mock_nova_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        project_id = 'fake_project'
        os_driver = sdk.OpenStackDriver('fake_region_2')
        total_quotas = os_driver.get_resource_usages(project_id)
        mock_nova_client().get_resource_usages.assert_called_once_with(
            project_id)
        mock_neutron_client().get_resource_usages.assert_called_once_with(
            project_id)
        mock_cinder_client().get_resource_usages.assert_called_once_with(
            project_id)
        self.assertIsNotNone(total_quotas)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_write_quota_limits(self, mock_keystone_client,
                                mock_cinder_client, mock_network_client,
                                mock_nova_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        project_id = 'fake_project'
        write_limits = {}
        write_limits['nova'] = {'ram': 1222, 'vcpus': 10, 'instances': 7}
        write_limits['cinder'] = {'disk': 1222}
        write_limits['neutron'] = {'network': 10, 'subnet': 10}
        os_driver = sdk.OpenStackDriver('fake_region_3')
        os_driver.write_quota_limits(project_id, write_limits)
        mock_nova_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      instances=7, ram=1222,
                                                      vcpus=10)
        mock_network_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      write_limits['neutron'])
        mock_cinder_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      **write_limits['cinder'])

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_delete_quota_limits(self, mock_cinder_client,
                                 mock_network_client, mock_nova_client,
                                 mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        project_id = 'fake_project'
        os_driver = sdk.OpenStackDriver('fake_region_4')
        os_driver.delete_quota_limits(project_id)
        mock_nova_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_network_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_cinder_client().delete_quota_limits.assert_called_once_with(
            project_id)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_enabled_projects(self, mock_cinder_client,
                                  mock_network_client, mock_nova_client,
                                  mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        input_project_list = ['project_1', 'project_2', 'project_3']
        os_driver = sdk.OpenStackDriver('fake_region_5')
        os_driver.keystone_client.get_enabled_projects.return_value = \
            input_project_list
        output_project_list = os_driver.get_enabled_projects()
        self.assertEqual(output_project_list, input_project_list)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_enabled_users(self, mock_cinder_client,
                               mock_network_client, mock_nova_client,
                               mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        user_1 = User('user1', '123')
        user_2 = User('user2', '456')
        input_users_list = [user_1, user_2]
        os_driver = sdk.OpenStackDriver('fake_region_5')
        os_driver.keystone_client.get_enabled_users.return_value = \
            input_users_list
        output_users_list = os_driver.get_enabled_users()
        self.assertEqual(output_users_list, input_users_list)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_cache_os_clients(self, mock_cinder_client,
                              mock_network_client, mock_nova_client,
                              mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        os_driver_1 = sdk.OpenStackDriver('RegionOne')
        os_driver_2 = sdk.OpenStackDriver('RegionTwo')
        os_driver_3 = sdk.OpenStackDriver('RegionOne')
        os_driver_4 = sdk.OpenStackDriver('RegionTwo')
        # assert equal for same region clients objects to test caching
        self.assertEqual(os_driver_1.nova_client, os_driver_3.nova_client)
        self.assertEqual(os_driver_1.cinder_client, os_driver_3.cinder_client)
        self.assertEqual(os_driver_1.neutron_client,
                         os_driver_3.neutron_client)
        self.assertEqual(os_driver_2.nova_client, os_driver_4.nova_client)
        self.assertEqual(os_driver_2.cinder_client, os_driver_4.cinder_client)
        self.assertEqual(os_driver_2.neutron_client,
                         os_driver_4.neutron_client)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_disabled_quotas(self, mock_cinder_client,
                                 mock_network_client, mock_nova_client,
                                 mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        input_disable_quotas = ["floating_ips", "security_groups",
                                "security_group_rules"]
        os_driver = sdk.OpenStackDriver('fake_region9')
        output_disabled_quotas = os_driver._get_disabled_quotas('fake_region9')
        self.assertIn(input_disable_quotas[0], output_disabled_quotas)
        self.assertIn(input_disable_quotas[1], output_disabled_quotas)
        self.assertIn(input_disable_quotas[2], output_disabled_quotas)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_filtered_regions(self, mock_cinder_client,
                                  mock_network_client, mock_nova_client,
                                  mock_keystone_client, mock_is_token_valid):
        mock_is_token_valid.return_value = True
        input_region_list = ['region_one', 'region_two']
        os_driver = sdk.OpenStackDriver()
        os_driver.keystone_client.get_filtered_region.return_value = \
            input_region_list
        output_project_list = os_driver._get_filtered_regions('fake_project')
        self.assertEqual(output_project_list, input_region_list)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'endpoint_cache')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_all_regions_for_project_without_filter(self,
                                                        mock_cinder_client,
                                                        mock_network_client,
                                                        mock_nova_client,
                                                        mock_keystone_client,
                                                        mock_endpoint,
                                                        mock_is_token_valid):
        mock_is_token_valid.return_value = True
        input_region_list = ['region_one', 'region_two']
        os_driver = sdk.OpenStackDriver()
        os_driver.keystone_client.get_filtered_region.return_value = []
        mock_endpoint.EndpointCache(
            ).get_all_regions.return_value = input_region_list
        output_project_list = os_driver.get_all_regions_for_project(
            'fake_project')
        self.assertEqual(output_project_list, input_region_list)

    @mock.patch.object(sdk.OpenStackDriver, '_is_token_valid')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_all_regions_for_project_with_filter(self, mock_cinder_client,
                                                     mock_network_client,
                                                     mock_nova_client,
                                                     mock_keystone_client,
                                                     mock_is_token_valid):
        mock_is_token_valid.return_value = True
        input_region_list = ['region_one', 'region_two']
        os_driver = sdk.OpenStackDriver()
        os_driver.keystone_client.get_filtered_region.return_value = \
            input_region_list
        output_project_list = os_driver.get_all_regions_for_project(
            'fake_project')
        self.assertEqual(output_project_list, input_region_list)

    @mock.patch.object(sdk.OpenStackDriver, 'os_clients_dict')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_is_token_valid(self, mock_cinder_client, mock_network_client,
                            mock_nova_client, mock_keystone_client,
                            mock_os_client):
        expiry_time = timeutils.utcnow() + timeutils.datetime.timedelta(
            seconds=60)
        expiry_time = expiry_time.strftime(timeutils.PERFECT_TIME_FORMAT)
        mock_os_client['keystone'].keystone_client.tokens. \
            validate.return_value = {'expires_at': expiry_time}
        os_driver = sdk.OpenStackDriver()
        expected = os_driver._is_token_valid()
        self.assertEqual(expected, True)

    @mock.patch.object(sdk.OpenStackDriver, 'os_clients_dict')
    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_is_token_valid_failure(self, mock_cinder_client,
                                    mock_network_client,
                                    mock_nova_client, mock_keystone_client,
                                    mock_os_client):
        expiry_time = timeutils.utcnow()
        expiry_time = expiry_time.strftime(timeutils.PERFECT_TIME_FORMAT)
        mock_os_client['keystone'].keystone_client.tokens. \
            validate.return_value = {'expires_at': expiry_time}
        os_driver = sdk.OpenStackDriver()
        expected = os_driver._is_token_valid()
        self.assertEqual(expected, False)
