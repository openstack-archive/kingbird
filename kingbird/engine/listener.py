# Copyright 2016 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import time

from kingbird.common.i18n import _
from kingbird.common.i18n import _LI
from kingbird.common import manager
from kingbird.engine.quota_manager import QuotaManager
from kingbird.engine import scheduler


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

scheduler_opts = [
    cfg.BoolOpt('periodic_enable',
                default=True,
                help='boolean value for enable/disenable periodic tasks'),
    cfg.IntOpt('periodic_interval',
               default=900,
               help='periodic time interval for automatic quota sync job')
]

scheduler_opt_group = cfg.OptGroup('scheduler')
cfg.CONF.register_group(scheduler_opt_group)
cfg.CONF.register_opts(scheduler_opts, group=scheduler_opt_group)


class EngineManager(manager.Manager):
    """Manages all the kb engine activities."""

    target = messaging.Target(version='1.0')

    def __init__(self, *args, **kwargs):
        self.qm = QuotaManager()
        self.TG = scheduler.ThreadGroupManager()
        self.periodic_enable = cfg.CONF.scheduler.periodic_enable
        self.periodic_interval = cfg.CONF.scheduler.periodic_interval
        LOG.debug(_('Engine initialization...'))

        super(EngineManager, self).__init__(service_name="engine_manager",
                                            *args, **kwargs)
        if self.periodic_enable:
            LOG.debug("Adding periodic tasks for the engine to perform")
            self.TG.add_timer(self.periodic_interval,
                              self.periodic_balance_all)

    def init_host(self):
        LOG.debug(_('Engine init_host...'))

        pass

    def cleanup_host(self):
        LOG.debug(_('Engine cleanup_host...'))

        pass

    def pre_start_hook(self):
        LOG.debug(_('Engine pre_start_hook...'))

        pass

    def post_start_hook(self):
        LOG.debug(_('Engine post_start_hook...'))

        pass

    def periodic_balance_all(self):
        # Automated Quota Sync for all the keystone projects
        LOG.info(_LI("Periodic quota sync job started at: %s"),
                 time.strftime("%c"))
        self.qm.periodic_balance_all()

    def quota_sync_for_project(self, ctx, project_id):
        # On Demand Quota Sync for a project, will be triggered by KB-API
        LOG.info(_LI("On Demand Quota Sync Called for: %s"),
                 project_id)
        self.qm.quota_sync_for_project(project_id)

    def get_total_usage_for_tenant(self, ctx, project_id):
        # Returns a dictionary containing nova, neutron &
        # cinder usages for the project
        LOG.info(_LI("Get total tenant usage called for: %s"),
                 project_id)
        return self.qm.get_total_usage_for_tenant(project_id)
