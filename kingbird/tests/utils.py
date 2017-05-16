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

import eventlet
import random
import sqlalchemy
import string
import uuid

from oslo_config import cfg
from oslo_db import options

from kingbird.common import context
from kingbird.db import api as db_api


get_engine = db_api.get_engine


class UUIDStub(object):
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.uuid4 = uuid.uuid4
        uuid_stub = lambda: self.value
        uuid.uuid4 = uuid_stub

    def __exit__(self, *exc_info):
        uuid.uuid4 = self.uuid4


UUIDs = (UUID1, UUID2, UUID3, UUID4, UUID5) = sorted([str(uuid.uuid4())
                                                     for x in range(5)])


def random_name():
    return ''.join(random.choice(string.ascii_uppercase)
                   for x in range(10))


def setup_dummy_db():
    options.cfg.set_defaults(options.database_opts, sqlite_synchronous=False)
    options.set_defaults(cfg.CONF, connection="sqlite://")
    engine = get_engine()
    db_api.db_sync(engine)
    engine.connect()


def reset_dummy_db():
    engine = get_engine()
    meta = sqlalchemy.MetaData()
    meta.reflect(bind=engine)

    for table in reversed(meta.sorted_tables):
        if table.name == 'migrate_version':
            continue
        engine.execute(table.delete())


def create_quota_limit(ctxt, **kwargs):
    values = {
        'project_id': UUID1,
        'resource': "ram",
        'limit': 10,
    }
    values.update(kwargs)
    return db_api.quota_create(ctxt, **values)


def dummy_context(user='test_username', tenant='test_project_id',
                  region_name=None):
    return context.RequestContext.from_dict({
        'auth_token': 'abcd1234',
        'user': user,
        'project': tenant,
        'is_admin': True,
        'region_name': region_name
    })


def wait_until_true(predicate, timeout=60, sleep=1, exception=None):
    with eventlet.timeout.Timeout(timeout, exception):
        while not predicate():
            eventlet.sleep(sleep)
