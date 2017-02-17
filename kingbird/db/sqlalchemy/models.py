# Copyright (c) 2015 Ericsson AB
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
SQLAlchemy models for kingbird data.
"""

from oslo_db.sqlalchemy import models

from sqlalchemy.orm import session as orm_session
from sqlalchemy import (Column, Integer, String, Boolean, schema)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from kingbird.common import consts

BASE = declarative_base()


def get_session():
    from kingbird.db.sqlalchemy import api as db_api

    return db_api.get_session()


class KingbirdBase(models.ModelBase,
                   models.SoftDeleteMixin,
                   models.TimestampMixin):
    """Base class for Kingbird Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def expire(self, session=None, attrs=None):
        if not session:
            session = orm_session.Session.object_session(self)
            if not session:
                session = get_session()
        session.expire(self, attrs)

    def refresh(self, session=None, attrs=None):
        """Refresh this object."""
        if not session:
            session = orm_session.Session.object_session(self)
            if not session:
                session = get_session()
        session.refresh(self, attrs)

    def delete(self, session=None):
        """Delete this object."""
        if not session:
            session = orm_session.Session.object_session(self)
            if not session:
                session = get_session()
        session.begin()
        session.delete(self)
        session.commit()


class Quota(BASE, KingbirdBase):
    """Represents a single quota override for a project.

    If there is no row for a given project id and resource, then the
    default for the quota class is used.  If there is no row for a
    given quota class and resource, then the default for the
    deployment is used. If the row is present but the hard limit is
    Null, then the resource is unlimited.
    """

    __tablename__ = 'quotas'

    __table_args__ = (
        schema.UniqueConstraint("project_id", "resource", "deleted",
                                name="uniq_quotas0project_id0resource0deleted"
                                ),)

    id = Column(Integer, primary_key=True)

    project_id = Column(String(255), index=True)

    resource = Column(String(255), nullable=False)

    hard_limit = Column(Integer, nullable=True)


class QuotaClass(BASE, KingbirdBase):
    """Represents a single quota override for a quota class.

    If there is no row for a given quota class and resource, then the
    default for the deployment is used.  If the row is present but the
    hard limit is Null, then the resource is unlimited.
    """

    __tablename__ = "quota_classes"

    id = Column(Integer, primary_key=True)

    class_name = Column(String(255), index=True)

    resource = Column(String(255))

    hard_limit = Column(Integer, nullable=True)


class SyncLock(BASE, KingbirdBase):
    """Store locks to avoid overlapping of projects

    syncing during automatic periodic sync jobs with
    multiple-engines.
    """

    __tablename__ = 'sync_lock'

    id = Column(Integer, primary_key=True)

    engine_id = Column(String(36), nullable=False)

    timer_lock = Column(String(255), nullable=False)

    task_type = Column(String(36), nullable=False)


class Service(BASE, KingbirdBase):
    """"Kingbird service engine registry"""

    __tablename__ = 'service'

    id = Column('id', String(36), primary_key=True, nullable=False)

    host = Column(String(255))

    binary = Column(String(255))

    topic = Column(String(255))

    disabled = Column(Boolean, default=False)

    disabled_reason = Column(String(255))


class SyncJob(BASE, KingbirdBase):
    """Kingbird Sync Job registry"""

    __tablename__ = 'sync_job'

    id = Column('id', String(36), primary_key=True)

    sync_status = Column(String(36), default=consts.JOB_PROGRESS,
                         nullable=False)

    job_relation = relationship('ResourceSync', backref='sync_job')

    user_id = Column('user_id', String(36), nullable=False)

    project_id = Column('project_id', String(36), nullable=False)


class ResourceSync(BASE, KingbirdBase):
    """ResourceSync_registry"""

    __tablename__ = 'resource_sync'

    job_id = Column('job_id', String(36),
                    ForeignKey('sync_job.id'), primary_key=True)

    source_region = Column('source_region', String(36), primary_key=True)

    target_region = Column('target_region', String(36), primary_key=True)

    resource = Column('resource', String(36), primary_key=True)

    resource_type = Column('resource_type', String(36), nullable=False)

    sync_status = Column(String(36), default=consts.JOB_PROGRESS,
                         nullable=False)
