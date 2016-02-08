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
from kingbird.engine.quota_manager import QuotaManager
from kingbird.tests import base
from kingbird.tests import utils


class TestEngineManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestEngineManager, self).setUp()
        self.context = utils.dummy_context()

    def test_init(self):
        engine_manager = listener.EngineManager()
        self.assertIsNotNone(engine_manager)
        self.assertIsInstance(engine_manager.qm, QuotaManager)

    def test_say_hello_world_call(self):
        payload = "test payload"
        engine_manager = listener.EngineManager()
        return_value = engine_manager.say_hello_world_call(self.context,
                                                           payload)
        expected_output = "payload: %s" % payload
        self.assertEqual(return_value, expected_output)

    def test_say_hello_world_cast(self):
        payload = "test payload"
        engine_manager = listener.EngineManager()
        return_value = engine_manager.say_hello_world_call(self.context,
                                                           payload)
        expected_output = "payload: %s" % payload
        self.assertEqual(return_value, expected_output)

    @mock.patch.object(listener, 'context')
    @mock.patch.object(listener, 'QuotaManager')
    def test_periodic_balance_all(self, mock_qm, mock_context):
        engine_manager = listener.EngineManager()
        cntxt = utils.dummy_context()
        mock_context.get_admin_context().return_value = cntxt
        engine_manager.periodic_balance_all()
        mock_qm().periodic_balance_all.assert_called_once_with(
            mock_context.get_admin_context())
