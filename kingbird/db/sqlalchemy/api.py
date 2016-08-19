# Copyright (c) 2015 Ericsson AB.
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

'''
Implementation of SQLAlchemy backend.
'''

import sys
import threading

from oslo_config import cfg
from oslo_db import api as oslo_db_api
from oslo_db.sqlalchemy import enginefacade

from oslo_log import log as logging
from oslo_utils import timeutils

from sqlalchemy.orm import joinedload_all

from kingbird.common import exceptions as exception
from kingbird.common.i18n import _
from kingbird.db.sqlalchemy import migration
from kingbird.db.sqlalchemy import models

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

_facade = None

_main_context_manager = None
_CONTEXT = threading.local()


def _get_main_context_manager():
    global _main_context_manager
    if not _main_context_manager:
        _main_context_manager = enginefacade.transaction_context()
    return _main_context_manager


def get_engine():
    return _get_main_context_manager().get_legacy_facade().get_engine()


def get_session():
    return _get_main_context_manager().get_legacy_facade().get_session()


def read_session():
    return _get_main_context_manager().reader.using(_CONTEXT)


def write_session():
    return _get_main_context_manager().writer.using(_CONTEXT)


_DEFAULT_QUOTA_NAME = 'default'


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def model_query(context, *args):
    with read_session() as session:
        query = session.query(*args).options(joinedload_all('*'))
        return query


def _session(context):
    return get_session()


def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    if not context:
        LOG.warning(_('Use of empty request context is deprecated'),
                    DeprecationWarning)
        raise Exception('die')
    return context.is_admin


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user or not context.tenant_id:
        return False
    return True


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.
    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)

    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`authorize_project_context` and
    :py:func:`authorize_user_context`.
    The first argument to the wrapped function must be the context.
    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)

    return wrapper


###################


@require_context
def _quota_get(context, project_id, resource, session=None):
    result = model_query(context, models.Quota). \
        filter_by(project_id=project_id). \
        filter_by(resource=resource). \
        first()

    if not result:
        raise exception.ProjectQuotaNotFound(project_id=project_id)

    return result


@require_context
def quota_get(context, project_id, resource):
    return _quota_get(context, project_id, resource)


@require_context
def quota_get_all_by_project(context, project_id):
    rows = model_query(context, models.Quota). \
        filter_by(project_id=project_id). \
        all()
    result = {'project_id': project_id}
    for row in rows:
        result[row.resource] = row.hard_limit
    return result


@require_admin_context
def quota_create(context, project_id, resource, limit):
    with write_session() as session:
        quota_ref = models.Quota()
        quota_ref.project_id = project_id
        quota_ref.resource = resource
        quota_ref.hard_limit = limit
        session.add(quota_ref)
        return quota_ref


@require_admin_context
def quota_update(context, project_id, resource, limit):
    with write_session() as session:
        quota_ref = _quota_get(context, project_id, resource, session=session)
        if not quota_ref:
            raise exception.ProjectQuotaNotFound(project_id=project_id)
        quota_ref.hard_limit = limit
        quota_ref.save(session)
        return quota_ref


@require_admin_context
def quota_destroy(context, project_id, resource):
    with write_session() as session:
        quota_ref = _quota_get(context, project_id, resource, session=session)
        if not quota_ref:
            raise exception.ProjectQuotaNotFound(project_id=project_id)
        session.delete(quota_ref)


@require_admin_context
def quota_destroy_all(context, project_id):
    with write_session() as session:

        quotas = model_query(context, models.Quota). \
            filter_by(project_id=project_id). \
            all()

        if not quotas:
            raise exception.ProjectQuotaNotFound(project_id=project_id)

        for quota_ref in quotas:
            session.delete(quota_ref)


##########################

@require_context
def _quota_class_get(context, class_name, resource):
    result = model_query(context, models.QuotaClass). \
        filter_by(deleted=False). \
        filter_by(class_name=class_name). \
        filter_by(resource=resource). \
        first()

    if not result:
        raise exception.QuotaClassNotFound(class_name=class_name)

    return result


@require_context
def quota_class_get(context, class_name, resource):
    return _quota_class_get(context, class_name, resource)


@require_context
def quota_class_get_default(context):
    return quota_class_get_all_by_name(context, _DEFAULT_QUOTA_NAME)


@require_context
def quota_class_get_all_by_name(context, class_name):
    rows = model_query(context, models.QuotaClass). \
        filter_by(deleted=False). \
        filter_by(class_name=class_name). \
        all()

    result = {'class_name': class_name}
    for row in rows:
        result[row.resource] = row.hard_limit

    return result


@require_admin_context
def quota_class_create(context, class_name, resource, limit):
    with write_session() as session:
        quota_class_ref = models.QuotaClass()
        quota_class_ref.class_name = class_name
        quota_class_ref.resource = resource
        quota_class_ref.hard_limit = limit
        session.add(quota_class_ref)
        return quota_class_ref


@require_admin_context
def quota_class_update(context, class_name, resource, limit):
    with write_session() as session:
        quota_class_ref = session.query(models.QuotaClass). \
            filter_by(deleted=False). \
            filter_by(class_name=class_name). \
            filter_by(resource=resource).first()
        if not quota_class_ref:
            raise exception.QuotaClassNotFound(class_name=class_name)
        quota_class_ref.hard_limit = limit
        quota_class_ref.save(session)
        return quota_class_ref


@require_admin_context
def quota_class_destroy(context, class_name, resource):
    with write_session() as session:
        quota_class_ref = _quota_class_get(context, class_name, resource)
        session.delete(quota_class_ref)


@require_admin_context
def quota_class_destroy_all(context, class_name):
    with write_session() as session:
        quota_classes = session.query(models.QuotaClass). \
            filter_by(deleted=False). \
            filter_by(class_name=class_name). \
            all()
        for quota_class_ref in quota_classes:
            session.delete(quota_class_ref)


def db_sync(engine, version=None):
    """Migrate the database to `version` or the most recent version."""
    return migration.db_sync(engine, version=version)


def db_version(engine):
    """Display the current database version."""
    return migration.db_version(engine)


@oslo_db_api.wrap_db_retry(max_retries=3, retry_on_deadlock=True,
                           retry_interval=0.5, inc_retry_interval=True)
def sync_lock_acquire(context, engine_id, task_type):
    with write_session() as session:
        lock = session.query(models.SyncLock). \
            filter_by(task_type=task_type).all()
        if not lock:
            lock_ref = models.SyncLock()
            lock_ref.engine_id = engine_id
            lock_ref.timer_lock = "Lock Acquired for EngineId: " + engine_id
            lock_ref.task_type = task_type
            session.add(lock_ref)
            return True
    return False


@oslo_db_api.wrap_db_retry(max_retries=3, retry_on_deadlock=True,
                           retry_interval=0.5, inc_retry_interval=True)
def sync_lock_release(context, task_type):
    with write_session() as session:
        locks = session.query(models.SyncLock). \
            filter_by(task_type=task_type).all()
        for lock in locks:
            session.delete(lock)


def sync_lock_steal(context, engine_id, task_type):
    sync_lock_release(context, task_type)
    return sync_lock_acquire(context, engine_id, task_type)


def service_create(context, service_id, host=None, binary=None,
                   topic=None):
    with write_session() as session:
        time_now = timeutils.utcnow()
        svc = models.Service(id=service_id,
                             host=host,
                             binary=binary,
                             topic=topic,
                             created_at=time_now,
                             updated_at=time_now)
        session.add(svc)
        return svc


def service_update(context, service_id, values=None):
    with write_session() as session:
        service = session.query(models.Service).get(service_id)
        if not service:
            return

        if values is None:
            values = {}

        values.update({'updated_at': timeutils.utcnow()})
        service.update(values)
        service.save(session)
        return service


def service_delete(context, service_id):
    with write_session() as session:
        session.query(models.Service).filter_by(
            id=service_id).delete(synchronize_session='fetch')

        # Remove all engine locks
        locks = session.query(models.SyncLock). \
            filter_by(engine_id=service_id).all()
        for lock in locks:
            session.delete(lock)


def service_get(context, service_id):
    return model_query(context, models.Service).get(service_id)


def service_get_all(context):
    return model_query(context, models.Service).all()
