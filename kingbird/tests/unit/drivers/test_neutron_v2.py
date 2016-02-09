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

import neutronclient

from kingbird.drivers.openstack import neutron_v2
from kingbird.tests import base
from kingbird.tests import utils


class TestNeutronClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestNeutronClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.session = 'fake_session'

    def test_init(self):
        neutron_client = neutron_v2.NeutronClient('fake_region',
                                                  self.session)
        self.assertIsNotNone(neutron_client)
        self.assertIsInstance(neutron_client.neutron_client,
                              neutronclient.v2_0.client.Client)

    def test_get_resource_usages(self):
        pass

    def test_update_quota_limits(self):
        pass

    def test_delete_quota_limits(self):
        pass
