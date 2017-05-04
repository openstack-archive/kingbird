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

from kingbird.drivers.openstack import glance_v2
from kingbird.tests import base
from kingbird.tests import utils


class TestGlanceClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestGlanceClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.endpoint = 'fake_endpoint'

    def test_init(self):
        glance_client = glance_v2.GlanceClient(self.endpoint, self.ctx)
        self.assertIsNotNone(glance_client)
