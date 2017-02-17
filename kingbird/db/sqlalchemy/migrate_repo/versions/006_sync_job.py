# Copyright (c) 2017 Ericsson AB.
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

from kingbird.common import consts


def upgrade(migrate_engine):
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine

    sync_job = sqlalchemy.Table(
        'sync_job', meta,
        sqlalchemy.Column('id', sqlalchemy.String(36),
                          primary_key=True),
        sqlalchemy.Column('sync_status', sqlalchemy.String(length=36),
                          default=consts.JOB_PROGRESS, nullable=False),
        sqlalchemy.Column('user_id', sqlalchemy.String(36),
                          nullable=False),
        sqlalchemy.Column('project_id', sqlalchemy.String(36),
                          nullable=False),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted', sqlalchemy.Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    resource_sync = sqlalchemy.Table(
        'resource_sync', meta,
        sqlalchemy.Column('job_id', sqlalchemy.String(36),
                          sqlalchemy.ForeignKey('sync_job.id'),
                          primary_key=True),
        sqlalchemy.Column('source_region', sqlalchemy.String(36),
                          primary_key=True),
        sqlalchemy.Column('target_region', sqlalchemy.String(36),
                          primary_key=True),
        sqlalchemy.Column('resource', sqlalchemy.String(36),
                          primary_key=True),
        sqlalchemy.Column('resource_type', sqlalchemy.String(36),
                          nullable=False),
        sqlalchemy.Column('sync_status', sqlalchemy.String(36),
                          default=consts.JOB_PROGRESS, nullable=False),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted_at', sqlalchemy.DateTime),
        sqlalchemy.Column('deleted', sqlalchemy.Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )
    sync_job.create()
    resource_sync.create()
