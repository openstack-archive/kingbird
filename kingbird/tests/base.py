# Copyright (c) 2015 Ericsson AB
# All Rights Reserved.
#
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

from kingbird.db import api as db_api
from kingbird.tests import utils
from oslo_config import cfg
from oslo_db import options
from oslotest import base
import sqlalchemy

get_engine = db_api.get_engine


class KingbirdTestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""


class KingbirdDbTestCase(base.BaseTestCase):
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

    def create_quota_limit(self, ctxt, **kwargs):
        values = {
            'project_id': utils.UUID1,
            'resource': "ram",
            'limit': 10,
        }
        values.update(kwargs)
        return db_api.quota_create(ctxt, **values)

    def setUp(self):
        super(KingbirdDbTestCase, self).setUp()

        self.setup_dummy_db()

        self.addCleanup(self.reset_dummy_db)
