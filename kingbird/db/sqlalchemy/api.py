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

from oslo_config import cfg
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log as logging

from kingbird.common import exceptions as exception
from kingbird.common.i18n import _
from kingbird.db.sqlalchemy import migration
from kingbird.db.sqlalchemy import models

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

_facade = None


def get_facade():
    global _facade

    if not _facade:
        _facade = db_session.EngineFacade.from_config(CONF)
    return _facade


get_engine = lambda: get_facade().get_engine()
get_session = lambda: get_facade().get_session()


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def model_query(context, *args):
    session = _session(context)
    query = session.query(*args)
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
    quota_ref = models.Quota()
    quota_ref.project_id = project_id
    quota_ref.resource = resource
    quota_ref.hard_limit = limit

    session = _session(context)
    with session.begin():
        quota_ref.save(session)
        return quota_ref


@require_admin_context
def quota_update(context, project_id, resource, limit):
    session = _session(context)
    with session.begin():
        quota_ref = _quota_get(context, project_id, resource, session=session)
        quota_ref.hard_limit = limit
        quota_ref.save(_session(context))
        return quota_ref


@require_admin_context
def quota_destroy(context, project_id, resource):
    session = _session(context)
    quota_ref = _quota_get(context, project_id, resource, session=session)
    quota_ref.delete(session=session)


@require_admin_context
def quota_destroy_all(context, project_id):
    session = _session(context)

    quotas = model_query(context, models.Quota). \
        filter_by(project_id=project_id). \
        all()

    if not quotas:
        raise exception.ProjectQuotaNotFound(project_id=project_id)

    for quota_ref in quotas:
        quota_ref.delete(session=session)


def db_sync(engine, version=None):
    """Migrate the database to `version` or the most recent version."""
    return migration.db_sync(engine, version=version)


def db_version(engine):
    """Display the current database version."""
    return migration.db_version(engine)
