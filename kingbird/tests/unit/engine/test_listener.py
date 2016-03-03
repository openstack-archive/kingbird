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

from kingbird.engine import listener
from kingbird.tests import base
from kingbird.tests import utils

FAKE_PROJECT = 'fake_project'


class TestEngineManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestEngineManager, self).setUp()
        self.context = utils.dummy_context()

    @mock.patch.object(listener, 'QuotaManager')
    def test_init(self, mock_qm):
        engine_manager = listener.EngineManager()
        self.assertIsNotNone(engine_manager)
        self.assertEqual(engine_manager.qm, mock_qm())

    @mock.patch.object(listener, 'QuotaManager')
    def test_periodic_balance_all(self, mock_qm):
        engine_manager = listener.EngineManager()
        engine_manager.periodic_balance_all()
        mock_qm().periodic_balance_all.assert_called_once_with()

    @mock.patch.object(listener, 'QuotaManager')
    def test_quota_sync_for_project(self, mock_qm):
        engine_manager = listener.EngineManager()
        engine_manager.quota_sync_for_project(self.context, FAKE_PROJECT)
        mock_qm().quota_sync_for_project.assert_called_once_with(FAKE_PROJECT)

    @mock.patch.object(listener, 'QuotaManager')
    def test_get_total_usage_for_tenant(self, mock_qm):
        engine_manager = listener.EngineManager()
        engine_manager.get_total_usage_for_tenant(self.context, FAKE_PROJECT)
        mock_qm().get_total_usage_for_tenant.assert_called_once_with(
            FAKE_PROJECT)
