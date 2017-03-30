# Copyright (c) 2015 Ericsson AB
# All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import sqlalchemy

from oslo_config import cfg
from oslo_db import options

from kingbird.common import config
from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils


config.register_options()
get_engine = api.get_engine
UUID1 = utils.UUID1
FAKE_TASK_TYPE = 'fake_sync'
FAKE_TASK_TYPE_2 = 'fake_sync2'


class DBAPISyncLockTest(base.KingbirdTestCase):
    def setup_dummy_db(self):
        options.cfg.set_defaults(options.database_opts,
                                 sqlite_synchronous=False)
        options.set_defaults(cfg.CONF, connection="sqlite://")
        engine = get_engine()
        db_api.db_sync(engine)
        engine.connect()

    def reset_dummy_db(self):
        engine = get_engine()
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=engine)

        for table in reversed(meta.sorted_tables):
            if table.name == 'migrate_version':
                continue
            engine.execute(table.delete())

    def acquire_lock(self, ctxt, FAKE_TASK_TYPE):
        return db_api.sync_lock_acquire(ctxt, utils.UUID1, FAKE_TASK_TYPE)

    def release_lock(self, ctxt, FAKE_TASK_TYPE):
        return db_api.sync_lock_release(ctxt, FAKE_TASK_TYPE)

    def steal_lock(self, ctxt, FAKE_TASK_TYPE):
        return db_api.sync_lock_steal(ctxt, utils.UUID1, FAKE_TASK_TYPE)

    def setUp(self):
        super(DBAPISyncLockTest, self).setUp()

        self.setup_dummy_db()
        self.addCleanup(self.reset_dummy_db)
        self.ctxt = utils.dummy_context()

    def test_sync_lock_acquire(self):
        expected_value = self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        self.assertEqual(expected_value, True)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)

    def test_sync_lock_release(self):
        self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)
        # Lock is released, Now check If we can acquire a lock
        lock = self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        self.assertEqual(lock, True)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)

    def test_sync_lock_acquire_fail_same_task_type(self):
        self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        second_lock = self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        # Lock cannot be acquired for second time as it is not released
        self.assertEqual(second_lock, False)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)

    def test_sync_lock_steal(self):
        expected_value = self.steal_lock(self.ctxt, FAKE_TASK_TYPE)
        self.assertEqual(expected_value, True)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)

    def test_sync_lock_steal_with_allready_acquired_lock(self):
        self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        steal_lock = self.steal_lock(self.ctxt, FAKE_TASK_TYPE)
        self.assertEqual(steal_lock, True)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)

    def test_sync_lock_acquire_with_different_task_type(self):
        expected_value = self.acquire_lock(self.ctxt, FAKE_TASK_TYPE)
        expected_value_2 = self.acquire_lock(self.ctxt, FAKE_TASK_TYPE_2)
        self.assertEqual(expected_value, True)
        self.assertEqual(expected_value_2, True)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE)
        self.release_lock(self.ctxt, FAKE_TASK_TYPE_2)
