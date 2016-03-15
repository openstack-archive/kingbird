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

import sqlalchemy


def upgrade(migrate_engine):
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine

    sync_lock = sqlalchemy.Table(
        'sync_lock', meta,
        sqlalchemy.Column('id', sqlalchemy.Integer,
                          primary_key=True, nullable=False),
        sqlalchemy.Column('timer_lock', sqlalchemy.String(length=255),
                          nullable=False),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted', sqlalchemy.Integer),
        sqlalchemy.Column('engine_id', sqlalchemy.String(length=36),
                          nullable=False),
        sqlalchemy.Column('task_type', sqlalchemy.String(length=36),
                          nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )
    sync_lock.create()
