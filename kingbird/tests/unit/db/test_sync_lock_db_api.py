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

from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils


get_engine = api.get_engine
UUID1 = utils.UUID1


class DBAPISyncLockTest(base.KingbirdTestCase):
    def setup_dummy_db(self):
        options.cfg.set_defaults(options.database_opts,
                                 sqlite_synchronous=False)
        options.set_defaults(cfg.CONF, connection="sqlite://",
                             sqlite_db='kingbird.db')
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

    def acquire_lock(self, ctxt):
        return db_api.sync_lock_acquire(ctxt, utils.UUID1)

    def release_lock(self, ctxt):
        return db_api.sync_lock_release(ctxt)

    def steal_lock(self, ctxt):
        return db_api.sync_lock_steal(ctxt, utils.UUID1)

    def setUp(self):
        super(DBAPISyncLockTest, self).setUp()

        self.setup_dummy_db()
        self.addCleanup(self.reset_dummy_db)
        self.ctxt = utils.dummy_context()

    def test_sync_lock_acquire(self):
        expected_value = self.acquire_lock(self.ctxt)
        self.assertEqual(expected_value, True)
        self.release_lock(self.ctxt)

    def test_sync_lock_release(self):
        self.acquire_lock(self.ctxt)
        self.release_lock(self.ctxt)
        # Lock is released, Now check If we can acquire a lock
        lock = self.acquire_lock(self.ctxt)
        self.assertEqual(lock, True)
        self.release_lock(self.ctxt)

    def test_sync_lock_acquire_fail(self):
        self.acquire_lock(self.ctxt)
        second_lock = self.acquire_lock(self.ctxt)
        # Lock cannot be acquired for second time as it is not released
        self.assertEqual(second_lock, False)
        self.release_lock(self.ctxt)

    def test_sync_lock_steal(self):
        expected_value = self.steal_lock(self.ctxt)
        self.assertEqual(expected_value, True)
        self.release_lock(self.ctxt)

    def test_sync_lock_steal_with_allready_acquired_lock(self):
        self.acquire_lock(self.ctxt)
        steal_lock = self.steal_lock(self.ctxt)
        self.assertEqual(steal_lock, True)
        self.release_lock(self.ctxt)
