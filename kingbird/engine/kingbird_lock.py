# Copyright 2016 Ericsson AB
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

from oslo_config import cfg
from oslo_log import log as logging

from kingbird.common.i18n import _
from kingbird.db import api as db_api
from kingbird.engine import scheduler


LOG = logging.getLogger(__name__)

lock_opts = [
    cfg.IntOpt('lock_retry_times',
               default=3,
               help=_('Number of times trying to grab a lock.')),
    cfg.IntOpt('lock_retry_interval',
               default=10,
               help=_('Number of seconds between lock retries.'))
]

lock_opts_group = cfg.OptGroup('locks')
cfg.CONF.register_group(lock_opts_group)
cfg.CONF.register_opts(lock_opts, group=lock_opts_group)


def sync_lock_acquire(context, engine_id, task_type, forced=False):
    """Try to lock with specified engine_id.

    :param engine: ID of the engine which wants to lock the projects.
    :returns: True if lock is acquired, or False otherwise.
    """

    # Step 1: try lock the projects- if it returns True then success
    LOG.info('Trying to acquire lock with %(engId)s for Task: %(task)s',
             {'engId': engine_id,
              'task': task_type
              }
             )
    lock_status = db_api.sync_lock_acquire(context, engine_id, task_type)
    if lock_status:
        return True

    # Step 2: retry using global configuration options
    retries = cfg.CONF.locks.lock_retry_times
    retry_interval = cfg.CONF.locks.lock_retry_interval

    while retries > 0:
        scheduler.sleep(retry_interval)
        LOG.info('Retry acquire lock with %(engId)s for Task: %(task)s',
                 {'engId': engine_id,
                  'task': task_type
                  }
                 )
        lock_status = db_api.sync_lock_acquire(context, engine_id, task_type)
        if lock_status:
            return True
        retries = retries - 1

    # Step 3: Last resort is 'forced locking', only needed when retry failed
    if forced:
        lock_status = db_api.sync_lock_steal(context, engine_id, task_type)
        if not lock_status:
            return False
        else:
            return True

    # Will reach here only when not able to acquire locks with retry

    LOG.error('Not able to acquire lock  for %(task)s with retry'
              ' with engineId %(engId)s',
              {'engId': engine_id,
               'task': task_type
               }
              )
    return False


def sync_lock_release(context, engine_id, task_type):
    """Release the lock for the projects"""

    LOG.info('Releasing acquired lock with %(engId)s for Task: %(task)s',
             {'engId': engine_id,
              'task': task_type
              }
             )
    return db_api.sync_lock_release(context, task_type)


def list_opts():
    yield lock_opts_group.name, lock_opts
