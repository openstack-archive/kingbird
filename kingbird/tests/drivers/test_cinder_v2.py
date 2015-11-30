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


class TestCinderClient(base.KingbirdTestCase):
    @mock.patch.object(sdk.OpenStackDriver, '_create_connection')
    def setUp(self, mock_os_client):
        super(TestCinderClient, self).setUp()
        self.cinder_client = mock_os_client.return_value.volume

    def test_init(self):
        pass

    def test_get_resource_usages(self):
        pass

    def test_update_quota_limits(self):
        pass

    def test_delete_quota_limits(self):
        pass
