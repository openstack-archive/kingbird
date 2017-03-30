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
from oslo_utils import uuidutils

from kingbird.common import config
from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils

config.register_options()
get_engine = api.get_engine


class ServiceRegistryTest(base.KingbirdTestCase):
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

    def setUp(self):
        super(ServiceRegistryTest, self).setUp()

        self.setup_dummy_db()
        self.addCleanup(self.reset_dummy_db)
        self.ctxt = utils.dummy_context()

    def _create_service(self, **kwargs):
        values = {
            'service_id': 'f9aff81e-bc1f-4119-941d-ad1ea7f31d19',
            'host': 'localhost',
            'binary': 'kingbird-engine',
            'topic': 'engine',
        }

        values.update(kwargs)
        return db_api.service_create(self.ctxt, **values)

    def test_service_create_get(self):
        service = self._create_service()
        ret_service = db_api.service_get(self.ctxt, service.id)
        self.assertIsNotNone(ret_service)
        self.assertEqual(service.id, ret_service.id)
        self.assertEqual(service.binary, ret_service.binary)
        self.assertEqual(service.host, ret_service.host)
        self.assertEqual(service.topic, ret_service.topic)
        self.assertEqual(service.disabled, ret_service.disabled)
        self.assertEqual(service.disabled_reason, ret_service.disabled_reason)
        self.assertIsNotNone(service.created_at)
        self.assertIsNotNone(service.updated_at)

    def test_service_get_all(self):
        values = []
        for i in range(4):
            values.append({'service_id': uuidutils.generate_uuid(),
                           'host': 'host-%s' % i})

        [self._create_service(**val) for val in values]

        services = db_api.service_get_all(self.ctxt)
        self.assertEqual(4, len(services))

    def test_service_update(self):
        old_service = self._create_service()
        old_updated_time = old_service.updated_at
        values = {'host': 'host-updated'}
        new_service = db_api.service_update(self.ctxt, old_service.id, values)
        self.assertEqual('host-updated', new_service.host)
        self.assertGreater(new_service.updated_at, old_updated_time)

    def test_service_update_values_none(self):
        old_service = self._create_service()
        old_updated_time = old_service.updated_at
        new_service = db_api.service_update(self.ctxt, old_service.id)
        self.assertGreater(new_service.updated_at, old_updated_time)

    def test_service_delete(self):
        service = self._create_service()
        db_api.service_delete(self.ctxt, service.id)
        res = db_api.service_get(self.ctxt, service.id)
        self.assertIsNone(res)
