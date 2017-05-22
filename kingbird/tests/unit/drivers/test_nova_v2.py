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
import novaclient

from kingbird.common import consts
from kingbird.drivers.openstack import nova_v2
from kingbird.tests import base
from kingbird.tests import utils


class Server(object):
    def __init__(self, id, metadata_items):
        self.metadata = metadata_items
        self.flavor = {}
        self.flavor['id'] = id


class Flavor(object):
    def __init__(self, id, ram, cores, disks):
        self.id = id
        self.ram = ram
        self.vcpus = cores
        self.disk = disks

s1 = Server(1, {'mkey': 'mvalue'})
s2 = Server(1, {'mkey': 'mvalue', 'm2key': 'm2value'})
FAKE_FLAVOR = Flavor(1, 512, 10, 50)
DISABLED_QUOTAS = ["floating_ips", "fixed_ips", "security_groups"]
FAKE_KEYPAIRS = ['key1', 'key2']
FAKE_LIMITS = {'absolute':
               {u'maxServerMeta': 100, u'maxPersonality': 5,
                u'totalServerGroupsUsed': 0,
                u'maxImageMeta': 100, u'maxPersonalitySize': 10240,
                u'maxTotalKeypairs': 100, u'maxSecurityGroupRules': 20,
                u'maxServerGroups': 10, u'totalCoresUsed': 2,
                u'totalRAMUsed': 1024, u'maxSecurityGroups': 10,
                u'totalFloatingIpsUsed': 0, u'totalInstancesUsed': 2,
                u'maxServerGroupMembers': 10, u'maxTotalFloatingIps': 10,
                u'totalSecurityGroupsUsed': 1, u'maxTotalInstances': 15,
                u'maxTotalRAMSize': 51200, u'maxTotalCores': 10
                }
               }
FAKE_RESOURCE_ID = 'fake_id'
DEFAULT_FORCE = False


class FakeKeypair(object):
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key


class TestNovaClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestNovaClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.session = 'fake_session'
        self.project = 'fake_project'
        self.user = 'fake_user'

    def test_init(self):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        self.assertIsNotNone(nv_client)
        expected_quotas = list(set(consts.NOVA_QUOTA_FIELDS) -
                               set(DISABLED_QUOTAS))
        self.assertEqual(nv_client.enabled_quotas, expected_quotas)
        self.assertIsInstance(nv_client.nova_client,
                              novaclient.v2.client.Client)

    @mock.patch.object(nova_v2, 'client')
    def test_get_resource_usages(self, mock_novaclient):
        mock_novaclient.Client().keypairs.list.return_value = FAKE_KEYPAIRS
        mock_novaclient.Client().limits.get().to_dict.return_value = \
            FAKE_LIMITS
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        total_nova_usage = nv_client.get_resource_usages(self.project)
        self.assertEqual(total_nova_usage['ram'], 512 * 2)
        self.assertEqual(total_nova_usage['cores'], 2)
        self.assertEqual(total_nova_usage['instances'], 2)
        self.assertEqual(total_nova_usage['key_pairs'], 2)

    @mock.patch.object(nova_v2, 'client')
    def test_update_quota_limits(self, mock_novaclient):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        new_quota = {'ram': 100, 'cores': 50}
        nv_client.update_quota_limits(self.project, **new_quota)
        mock_novaclient.Client().quotas.update.assert_called_once_with(
            self.project, **new_quota)

    @mock.patch.object(nova_v2, 'client')
    def test_delete_quota_limits(self, mock_novaclient):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)

        new_quota = {'ram': 100, 'cores': 50}
        nv_client.update_quota_limits(self.project, **new_quota)

        nv_client.delete_quota_limits(self.project)

        mock_novaclient.Client().quotas.delete.assert_called_once_with(
            self.project)

    @mock.patch.object(nova_v2, 'client')
    def test_get_keypairs(self, mock_novaclient):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        nv_client.get_keypairs(FAKE_RESOURCE_ID)
        mock_novaclient.Client().keypairs.get.return_value = 'key1'
        mock_novaclient.Client().keypairs.get.\
            assert_called_once_with(FAKE_RESOURCE_ID)

    @mock.patch.object(nova_v2, 'client')
    def test_create_keypairs_with_force_false(self, mock_novaclient):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        nv_client.create_keypairs(DEFAULT_FORCE, fake_key)
        self.assertEqual(0,
                         mock_novaclient.Client().keypairs.delete.call_count)
        mock_novaclient.Client().keypairs.create.\
            assert_called_once_with(fake_key.name,
                                    public_key=fake_key.public_key)

    @mock.patch.object(nova_v2, 'client')
    def test_create_keypairs_with_force_true(self, mock_novaclient):
        nv_client = nova_v2.NovaClient('fake_region', self.session,
                                       DISABLED_QUOTAS)
        fake_key = FakeKeypair('fake_name', 'fake-rsa')
        nv_client.create_keypairs(True, fake_key)
        mock_novaclient.Client().keypairs.delete.\
            assert_called_once_with(fake_key)
        mock_novaclient.Client().keypairs.create.\
            assert_called_once_with(fake_key.name,
                                    public_key=fake_key.public_key)
