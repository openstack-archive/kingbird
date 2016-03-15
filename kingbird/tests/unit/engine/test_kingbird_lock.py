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
import uuid

from oslo_config import cfg

from kingbird.common import config
from kingbird.engine import kingbird_lock
from kingbird.tests import base
from kingbird.tests import utils

config.register_options()
FAKE_ENGINE_ID = str(uuid.uuid4())
FAKE_TASK_TYPE = 'fake_sync'

cfg.CONF.import_group("locks", "kingbird.engine.kingbird_lock")
cfg.CONF.import_group("locks", "kingbird.engine.kingbird_lock")
cfg.CONF.set_override('lock_retry_times', 2, group='locks')
cfg.CONF.set_override('lock_retry_interval', 1, group='locks')


class TestKingbirdLock(base.KingbirdTestCase):
    def setUp(self):
        super(TestKingbirdLock, self).setUp()
        self.context = utils.dummy_context()

    @mock.patch.object(kingbird_lock, 'db_api')
    def test_sync_lock_acquire(self, mock_db_api):
        mock_db_api.sync_lock_acquire.return_value = "Fake Record"
        expected_value = kingbird_lock.sync_lock_acquire(
            self.context, FAKE_ENGINE_ID, FAKE_TASK_TYPE)
        self.assertEqual(expected_value, True)

    @mock.patch.object(kingbird_lock, 'db_api')
    def test_sync_lock_acquire_force_yes(self, mock_db_api):
        mock_db_api.sync_lock_acquire.return_value = False
        mock_db_api.db_api.sync_lock_steal.return_value = True
        expected_value = kingbird_lock.sync_lock_acquire(
            self.context, FAKE_ENGINE_ID, FAKE_TASK_TYPE, True)
        self.assertEqual(expected_value, True)

    @mock.patch.object(kingbird_lock, 'db_api')
    def test_sync_lock_release(self, mock_db_api):
        kingbird_lock.sync_lock_release(self.context, FAKE_ENGINE_ID,
                                        FAKE_TASK_TYPE)
        mock_db_api.sync_lock_release.assert_called_once_with(self.context,
                                                              FAKE_TASK_TYPE)

    @mock.patch.object(kingbird_lock, 'db_api')
    def test_sync_lock_acquire_fail(self, mock_db_api):
        mock_db_api.sync_lock_acquire.return_value = False
        expected_value = kingbird_lock.sync_lock_acquire(
            self.context, FAKE_ENGINE_ID, FAKE_TASK_TYPE)
        self.assertEqual(expected_value, False)
