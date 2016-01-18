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

from kingbird.drivers.openstack import sdk
from kingbird.tests import base
from kingbird.tests import utils


class TestOpenStackDriver(base.KingbirdTestCase):
    def setUp(self):
        super(TestOpenStackDriver, self).setUp()

        self.context = utils.dummy_context()
        self.nova_client = None
        self.cinder_client = None
        self.neutron_client = None
        self.keystone_client = None

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_init(self, mock_keystone_client, mock_cinder_client,
                  mock_neutron_client, mock_nova_client):
        os_driver = sdk.OpenStackDriver('fake_region_1')
        self.assertIsNotNone(os_driver.neutron_client)
        self.assertIsNotNone(os_driver.nova_client)
        self.assertIsNotNone(os_driver.keystone_client)
        self.assertIsNotNone(os_driver.cinder_client)

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_get_resource_usages(self, mock_keystone_client,
                                 mock_cinder_client, mock_neutron_client,
                                 mock_nova_client):
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

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_write_quota_limits(self, mock_keystone_client,
                                mock_cinder_client, mock_network_client,
                                mock_nova_client):
        project_id = 'fake_project'
        write_limits = {}
        write_limits['nova'] = {'ram': 1222, 'vcpus': 10, 'instances': 7}
        write_limits['cinder'] = {'disk': 1222}
        write_limits['neutron'] = {'network': 10, 'subnet': 10}
        os_driver = sdk.OpenStackDriver('fake_region_3')
        os_driver.write_quota_limits(project_id, write_limits)
        mock_nova_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      write_limits['nova'])
        mock_network_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      write_limits['neutron'])
        mock_cinder_client(
        ).update_quota_limits.assert_called_once_with(project_id,
                                                      write_limits['cinder'])

    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_delete_quota_limits(self, mock_cinder_client,
                                 mock_network_client, mock_nova_client,
                                 mock_keystone_client):
        project_id = 'fake_project'
        os_driver = sdk.OpenStackDriver('fake_region_4')
        os_driver.delete_quota_limits(project_id)
        mock_nova_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_network_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_cinder_client().delete_quota_limits.assert_called_once_with(
            project_id)

    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_get_enabled_projects(self, mock_cinder_client,
                                  mock_network_client, mock_nova_client,
                                  mock_keystone_client):
        input_project_list = ['project_1', 'project_2', 'project_3']
        os_driver = sdk.OpenStackDriver('fake_region_5')
        os_driver.keystone_client.get_enabled_projects.return_value = \
            input_project_list
        output_project_list = os_driver.get_enabled_projects()
        self.assertEqual(output_project_list, input_project_list)

    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    def test_cache_os_clients(self, mock_cinder_client,
                              mock_network_client, mock_nova_client,
                              mock_keystone_client):
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
