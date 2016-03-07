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

from kingbird.common import exceptions
from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils


get_engine = api.get_engine
UUID1 = utils.UUID1
UUID2 = utils.UUID2
UUID3 = utils.UUID3


class DBAPIQuotaTest(base.KingbirdTestCase):
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
        super(DBAPIQuotaTest, self).setUp()

        self.setup_dummy_db()
        self.addCleanup(self.reset_dummy_db)
        self.ctx = utils.dummy_context()

    def test_create_quota_limit(self):
        project_id = UUID2
        resource = 'cores'
        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        cores_limit = db_api.quota_get(self.ctx, project_id, resource)
        self.assertIsNotNone(cores_limit)
        self.assertEqual(15, cores_limit.hard_limit)

    def test_update_quota_limit(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        updated = db_api.quota_update(self.ctx, project_id, resource, 10)
        self.assertIsNotNone(updated)

        updated_limit = db_api.quota_get(self.ctx, project_id, resource)
        self.assertEqual(10, updated_limit.hard_limit)

    def test_delete_quota_limit(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        db_api.quota_destroy(self.ctx, project_id, resource)

        self.assertRaises(exceptions.ProjectQuotaNotFound,
                          db_api.quota_get,
                          self.ctx, project_id, resource)

    def test_delete_all_quota_limit(self):
        project_id = UUID2
        resources = [('cores', 2), ('ram', 2)]

        for r in resources:
            self.create_quota_limit(self.ctx,
                                    project_id=project_id,
                                    resource=r[0],
                                    limit=r[1])

        db_api.quota_destroy_all(self.ctx, project_id)

        for r in resources:
            self.assertRaises(exceptions.ProjectQuotaNotFound,
                              db_api.quota_get,
                              self.ctx, project_id, r[0])

    def test_quota_get_by_project(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        by_project = db_api.quota_get_all_by_project(self.ctx, project_id)
        self.assertIsNotNone(by_project)
        self.assertEqual(project_id, by_project['project_id'])

    def test_quota_get_by_nonexisting_project(self):
        project_id = UUID2
        expected_quota_set = {'project_id': project_id}
        project_limit = db_api.quota_get_all_by_project(self.ctx, project_id)
        self.assertEqual(project_limit, expected_quota_set)
