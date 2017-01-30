# Copyright (c) 2017 Ericsson AB
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

import oslo_db
import sqlalchemy

from oslo_config import cfg
from oslo_db import options

from kingbird.common import config
from kingbird.common import exceptions
from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils

config.register_options()
get_engine = api.get_engine
UUID1 = utils.UUID1


class DBAPIResourceSyncTest(base.KingbirdTestCase):
    def setup_dummy_db(self):
        options.cfg.set_defaults(options.database_opts,
                                 sqlite_synchronous=False)
        options.set_defaults(cfg.CONF, connection="sqlite://",
                             sqlite_db='kingbird.db')
        engine = get_engine()
        db_api.db_sync(engine)
        engine.connect()

    @staticmethod
    def reset_dummy_db():
        engine = get_engine()
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=engine)

        for table in reversed(meta.sorted_tables):
            if table.name == 'migrate_version':
                continue
            engine.execute(table.delete())

    @staticmethod
    def sync_job_create(ctxt, **kwargs):
        return db_api.sync_job_create(ctxt, **kwargs)

    @staticmethod
    def resource_sync_create(ctxt, **kwargs):
        return db_api.resource_sync_create(ctxt, **kwargs)

    def setUp(self):
        super(DBAPIResourceSyncTest, self).setUp()

        self.setup_dummy_db()
        self.addCleanup(self.reset_dummy_db)
        self.ctx = utils.dummy_context()

    def test_create_sync_job(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        self.assertEqual("IN_PROGRESS", job.sync_status)
        created_job = db_api.sync_job_list_by_user(self.ctx, "list")
        self.assertEqual("IN_PROGRESS", created_job[0].get('sync_status'))

    def test_primary_key_sync_job(self):
        self.sync_job_create(self.ctx, job_id=UUID1,
                             status="IN_PROGRESS")
        self.assertRaises(oslo_db.exception.DBDuplicateEntry,
                          self.sync_job_create, self.ctx, job_id=UUID1,
                          status="IN_PROGRESS")

    def test_sync_job_update(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        db_api.sync_job_update(self.ctx, UUID1, 'SUCCESS')
        updated_job = db_api.sync_job_list_by_user(self.ctx, 'list')
        self.assertEqual("SUCCESS", updated_job[0].get('sync_status'))

    def test_active_jobs(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        query = db_api.sync_job_list_by_user(self.ctx, 'active')
        self.assertEqual(query[0].get('sync_status'), job.sync_status)

    def test_update_invalid_job(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        self.assertRaises(exceptions.JobNotFound,
                          db_api.sync_job_update, self.ctx, 'fake_job',
                          'SUCCESS')

    def test_resource_sync_create(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        resource_sync_create = self.resource_sync_create(
            self.ctx, job=job, region='Fake_region',
            resource='fake_key', resource_type='keypair',
            status="IN_PROGRESS")
        self.assertIsNotNone(resource_sync_create)
        self.assertEqual("IN_PROGRESS", resource_sync_create.sync_status)
        created_job = db_api.resource_sync_list_by_job(self.ctx, job.id)
        self.assertEqual("IN_PROGRESS", created_job[0].get('sync_status'))

    def test_resource_sync_update(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        resource_sync_create = self.resource_sync_create(
            self.ctx, job=job, region='Fake_region',
            resource='fake_key', resource_type='keypair',
            status="IN_PROGRESS")
        resource_sync_create = self.resource_sync_create(
            self.ctx, job=job, region='Fake_region',
            resource='fake_key2', resource_type='keypair',
            status="IN_PROGRESS")
        self.assertIsNotNone(resource_sync_create)
        self.assertEqual("IN_PROGRESS", resource_sync_create.sync_status)
        db_api.resource_sync_update(
            self.ctx, job.id, 'Fake_region', 'fake_key', "SUCCESS")
        updated_job = db_api.resource_sync_list_by_job(self.ctx, job.id)
        self.assertEqual("SUCCESS", updated_job[0].get('sync_status'))

    def test_foreign_key(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        resource_sync_create = self.resource_sync_create(
            self.ctx, job=job, region='Fake_region', resource='fake_key',
            resource_type='keypair', status='IN_PROGRESS')
        self.assertIsNotNone(resource_sync_create)
        self.assertEqual(job.id, resource_sync_create.job_id)

    def test_delete_sync_job(self):
        job_id = UUID1
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.assertIsNotNone(job)
        self.resource_sync_create(
            self.ctx, job=job, region='Fake_region', resource='fake_key',
            resource_type='keypair', status='IN_PROGRESS')
        db_api.sync_job_delete(self.ctx, job_id)
        updated_job = db_api.sync_job_list_by_user(self.ctx, action='list')
        self.assertEqual(0, len(updated_job))

    def test_composite_primary_key(self):
        job = self.sync_job_create(self.ctx, job_id=UUID1,
                                   status="IN_PROGRESS")
        self.resource_sync_create(
            self.ctx, job=job, region='Fake_region', resource='fake_key',
            resource_type='keypair', status="IN_PROGRESS")
        self.assertRaises(oslo_db.exception.DBDuplicateEntry,
                          self.resource_sync_create, self.ctx, job=job,
                          region='Fake_region', resource='fake_key',
                          resource_type='keypair', status="IN_PROGRESS")
