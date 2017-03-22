# Copyright (c) 2015 Ericsson AB.
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

import datetime
from oslo_config import cfg
import sqlalchemy

CLASS_NAME = 'default'
CREATED_AT = datetime.datetime.now()

CONF = cfg.CONF
CONF.import_group('kingbird_global_limit', 'kingbird.common.config')


def upgrade(migrate_engine):
    """Add default quota class data into DB."""
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine

    quota_classes = sqlalchemy.Table('quota_classes', meta, autoload=True)

    rows = quota_classes.count(). \
        where(quota_classes.c.class_name == 'default').execute().scalar()

    # Do not add entries if there are already 'default' entries.  We don't
    # want to write over something the user added.
    if rows:
        return

    # Set default quota limits
    qci = quota_classes.insert()
    for resource, default in CONF.kingbird_global_limit.items():
        qci.execute({'created_at': CREATED_AT,
                     'class_name': CLASS_NAME,
                     'resource': resource[6:],
                     'hard_limit': default,
                     'deleted': False})
