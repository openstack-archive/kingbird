# Copyright (c) 2016 Ericsson AB
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

from kingbird.drivers.openstack import neutron_v2
from kingbird.tests import base
from kingbird.tests import utils


FAKE_EXTENSIONS = {
    'extensions': [{'name': 'fake_extension1', 'alias': 'fake_alias1'},
                   {'name': 'fake_extension2', 'alias': 'fake_alias2'}]
    }
FAKE_NETWORKS = {'networks': ['net1', 'net2']}
FAKE_SUBNETS = {'subnets': ['subnet1', 'subnet2']}
FAKE_PORTS = {'ports': ['port1', 'port2']}
FAKE_ROUTERS = {'routers': ['router1', 'router2']}
FAKE_FLOATINGIPS = {'floatingips': ['fp1', 'fp2']}
FAKE_SEC_GRP_RULES = {'security_group_rules': ['sec_grp_rul1', 'sec_grp_rul2']}
FAKE_SEC_GRP = {'security_groups': ['sec_grp1', 'sec_grp2']}


class TestNeutronClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestNeutronClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.session = 'fake_session'
        self.project = 'fake_project'
        self.disabled_quota = ['floating_ips', 'volumes']

    @mock.patch.object(neutron_v2, 'client')
    def test_init(self, mock_neutron):
        mock_neutron.Client().list_extensions.return_value = FAKE_EXTENSIONS
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        self.assertIsNotNone(neutron_client.neutron)
        self.assertEqual(FAKE_EXTENSIONS,
                         neutron_client.extension_list)

    @mock.patch.object(neutron_v2, 'client')
    def test_is_extension_supported(self, mock_neutron):
        mock_neutron.Client().list_extensions.return_value = FAKE_EXTENSIONS
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        actual_value = neutron_client.is_extension_supported('fake_alias1')
        self.assertEqual(True, actual_value)

    @mock.patch.object(neutron_v2, 'client')
    def test_extension_not_supported(self, mock_neutron):
        mock_neutron.Client().list_extensions.return_value = FAKE_EXTENSIONS
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        actual_value = neutron_client.is_extension_supported(
            'not_supported_alias')
        self.assertEqual(False, actual_value)

    @mock.patch.object(neutron_v2, 'client')
    def test_get_resource_usages(self, mock_neutron):
        mock_neutron.Client().list_networks.return_value = FAKE_NETWORKS
        mock_neutron.Client().list_subnets.return_value = FAKE_SUBNETS
        mock_neutron.Client().list_ports.return_value = FAKE_PORTS
        mock_neutron.Client().list_routers.return_value = FAKE_ROUTERS
        mock_neutron.Client().list_floatingips.return_value = FAKE_FLOATINGIPS
        mock_neutron.Client().list_security_group_rules.return_value = \
            FAKE_SEC_GRP_RULES
        mock_neutron.Client().list_security_groups.return_value = FAKE_SEC_GRP
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        setattr(neutron_client, 'is_sec_group_enabled', True)
        total_neutron_usages = neutron_client.get_resource_usages(
            self.project)
        self.assertEqual(2, total_neutron_usages['port'])
        self.assertEqual(2, total_neutron_usages['router'])
        self.assertEqual(2, total_neutron_usages['security_group'])
        self.assertEqual(2, total_neutron_usages['security_group_rule'])
        self.assertEqual(2, total_neutron_usages['floatingip'])
        self.assertEqual(2, total_neutron_usages['network'])
        self.assertEqual(2, total_neutron_usages['subnet'])

    @mock.patch.object(neutron_v2, 'client')
    def test_update_quota_limits(self, mock_neutron):
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        new_quota = {'subnets': 4, 'ports': 3}
        setattr(neutron_client, 'no_network', False)
        neutron_client.update_quota_limits(self.project, new_quota)
        mock_neutron.Client().update_quota.assert_called_once_with(
            self.project, {"quota": new_quota})

    @mock.patch.object(neutron_v2, 'client')
    def test_delete_quota_limits(self, mock_neutron):
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.disabled_quota,
                                                  self.session)
        setattr(neutron_client, 'no_network', False)
        neutron_client.delete_quota_limits(self.project)
        mock_neutron.Client().delete_quota.assert_called_once_with(
            self.project)
