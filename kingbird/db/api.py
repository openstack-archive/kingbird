# Copyright (c) 2015 Ericsson AB.
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
'''
Interface for database access.

SQLAlchemy is currently the only supported backend.
'''

from oslo_config import cfg
from oslo_db import api

CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'kingbird.db.sqlalchemy.api'}

IMPL = api.DBAPI.from_config(CONF, backend_mapping=_BACKEND_MAPPING)


def get_engine():
    return IMPL.get_engine()


def get_session():
    return IMPL.get_session()


# quota usage db methods

###################


def quota_create(context, project_id, resource, limit):
    """Create a quota for the given project and resource."""
    return IMPL.quota_create(context, project_id, resource, limit)


def quota_get(context, project_id, resource):
    """Retrieve a quota or raise if it does not exist."""
    return IMPL.quota_get(context, project_id, resource)


def quota_get_all_by_project(context, project_id):
    """Retrieve all quotas associated with a given project."""
    return IMPL.quota_get_all_by_project(context, project_id)


def quota_update(context, project_id, resource, limit):
    """Update a quota or raise if it does not exist."""
    return IMPL.quota_update(context, project_id, resource, limit)


def quota_destroy(context, project_id, resource):
    """Destroy the quota or raise if it does not exist."""
    return IMPL.quota_destroy(context, project_id, resource)


def quota_destroy_all(context, project_id):
    """Destroy the quota or raise if it does not exist."""
    return IMPL.quota_destroy(context, project_id)


def quota_class_get(context, class_name, resource):
    """Retrieve quota from the given quota class."""
    return IMPL.quota_class_get(context, class_name, resource)


def quota_class_get_default(context):
    """Get default class quotas."""
    return IMPL.quota_class_get_default(context)


def quota_class_get_all_by_name(context, class_name):
    """Get all quota limits for a specified class."""
    return IMPL.quota_class_get_all_by_name(context, class_name)


def quota_class_create(context, class_name, resource, limit):
    """Create a new quota limit in a specified class."""
    return IMPL.quota_class_create(context, class_name, resource, limit)


def quota_class_destroy_all(context, class_name):
    """Destroy all quotas for class."""
    return IMPL.quota_class_destroy_all(context, class_name)


def quota_class_update(context, class_name, resource, limit):
    """Update a quota or raise if it doesn't exist."""
    return IMPL.quota_class_update(context, class_name, resource, limit)


def db_sync(engine, version=None):
    """Migrate the database to `version` or the most recent version."""
    return IMPL.db_sync(engine, version=version)


def db_version(engine):
    """Display the current database version."""
    return IMPL.db_version(engine)


def sync_lock_acquire(context, engine_id, task_type):
    return IMPL.sync_lock_acquire(context, engine_id, task_type)


def sync_lock_release(context, task_type):
    return IMPL.sync_lock_release(context, task_type)


def sync_lock_steal(context, engine_id, task_type):
    return IMPL.sync_lock_steal(context, engine_id, task_type)


def service_create(context, service_id, host=None, binary=None,
                   topic=None):
    return IMPL.service_create(context, service_id=service_id, host=host,
                               binary=binary, topic=topic)


def service_update(context, service_id, values=None):
    return IMPL.service_update(context, service_id, values=values)


def service_delete(context, service_id):
    return IMPL.service_delete(context, service_id)


def service_get(context, service_id):
    return IMPL.service_get(context, service_id)


def service_get_all(context):
    return IMPL.service_get_all(context)


def sync_job_create(context, job_id):
    return IMPL.sync_job_create(context, job_id)


def sync_job_list(context, action=None):
    return IMPL.sync_job_list(context, action)


def sync_job_status(context, job_id):
    return IMPL.sync_job_status(context, job_id)


def sync_job_update(context, job_id, status):
    return IMPL.sync_job_status(context, job_id, status)


def sync_job_delete(context, job_id):
    return IMPL.sync_job_delete(context, job_id)


def resource_sync_create(context, job, region, source_region, resource,
                         resource_type):
    return IMPL.resource_sync_create(context, job, region, source_region,
                                     resource, resource_type)


def resource_sync_update(context, job_id, region, resource, status):
    return IMPL.resource_sync_update(context, job_id, region, resource,
                                     status)


def resource_sync_status(context, job_id):
    return IMPL.resource_sync_status(context, job_id)


def resource_sync_list_by_job(context, job_id):
    return IMPL.resource_sync_list_by_job(context, job_id)
