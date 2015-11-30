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
        self.region_name = 'RegionOne'
        self.os_client = None

    @mock.patch.object(sdk.OpenStackDriver, '_create_connection')
    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'KeystoneClient')
    def test_init(self, mock_keystone_client, mock_cinder_client,
                  mock_neutron_client, mock_nova_client, mock_os_client):
        sdk.OpenStackDriver(self.context, self.region_name)
        self.os_client = mock_os_client.return_value

        mock_os_client.assert_called_once_with(self.context, self.region_name)
        mock_nova_client.assert_called_once_with(self.os_client.compute)
        mock_neutron_client.assert_called_once_with(self.os_client.network)
        mock_cinder_client.assert_called_once_with(self.os_client.volume)
        mock_keystone_client.assert_called_once_with(self.os_client.identity)

    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_connection(self, mock_cm, mock_cloud_config, mock_argparse):
        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
        os_driver._create_connection(self.context,
                                     self.region_name)

        mock_argparse.ArgumentParser.assert_called_with()
        parser = mock_argparse.return_value
        cloud = mock_cloud_config.OpenStackConfig().get_one_cloud.return_value

        mock_cloud_config.OpenStackConfig.assert_called_with()
        mock_cm.build_plugin_option_parser(parser
                                           ).parse_args.assert_called_with()
        mock_cm.ClientManager.assert_called_with(cli_options=cloud,
                                                 api_version={}, verify=True)

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_get_resource_usages(self, mock_clientmanager, mock_cloud_config,
                                 mock_argparse, mock_cinder_client,
                                 mock_neutron_client, mock_nova_client):
        project_id = 'fake_project'
        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
        total_quotas = os_driver.get_resource_usages(project_id)
        mock_nova_client().get_resource_usages.assert_called_once_with(
            project_id)
        mock_neutron_client().get_resource_usages.assert_called_once_with(
            project_id)
        mock_cinder_client().get_resource_usages.assert_called_once_with(
            project_id)

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_write_quota_limits(self, mock_clientmanager, mock_cloud_config,
                                mock_argparse, mock_cinder_client,
                                mock_network_client, mock_nova_client):
        project_id = 'fake_project'
        write_limits = {}
        write_limits['nova'] = {'ram': 1222, 'vcpus': 10, 'instances': 7}
        write_limits['cinder'] = {'disk': 1222}
        write_limits['neutron'] = {'network': 10, 'subnet': 10}
        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
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

    @mock.patch.object(sdk, 'NovaClient')
    @mock.patch.object(sdk, 'NeutronClient')
    @mock.patch.object(sdk, 'CinderClient')
    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_delete_quota_limit(self, mock_clientmanager, mock_cloud_config,
                                mock_argparse, mock_cinder_client,
                                mock_network_client, mock_nova_client):
        project_id = 'fake_project'

        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
        os_driver.delete_quota_limit(project_id)
        mock_nova_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_network_client().delete_quota_limits.assert_called_once_with(
            project_id)
        mock_cinder_client().delete_quota_limits.assert_called_once_with(
            project_id)

    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_get_all_regions(self, mock_clientmanager, mock_cloud_config,
                             mock_argparse, mock_keystone_client):
        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
        os_driver.get_all_regions()
        mock_keystone_client().get_regions.assert_called_once_with()

    @mock.patch.object(sdk, 'KeystoneClient')
    @mock.patch.object(sdk, 'argparse')
    @mock.patch.object(sdk, 'cloud_config')
    @mock.patch.object(sdk, 'clientmanager')
    def test_get_enabled_projects(self, mock_clientmanager, mock_cloud_config,
                                  mock_argparse, mock_keystone_client):
        os_driver = sdk.OpenStackDriver(self.context, self.region_name)
        os_driver.get_enabled_projects()
        mock_keystone_client().get_enabled_projects.assert_called_once_with()
