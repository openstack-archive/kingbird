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

import six
import time
import uuid

import functools
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging


from kingbird.common import consts
from kingbird.common import context
from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.common.i18n import _LE
from kingbird.common.i18n import _LI
from kingbird.common import messaging as rpc_messaging
from kingbird.engine.quota_manager import QuotaManager

from kingbird.engine import scheduler

from oslo_service import service

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def request_context(func):
    @functools.wraps(func)
    def wrapped(self, ctx, *args, **kwargs):
        if ctx is not None and not isinstance(ctx, context.RequestContext):
            ctx = context.RequestContext.from_dict(ctx.to_dict())
        try:
            return func(self, ctx, *args, **kwargs)
        except exceptions.KingbirdException:
            raise oslo_messaging.rpc.dispatcher.ExpectedException()

    return wrapped


class EngineService(service.Service):
    '''Lifecycle manager for a running service engine.

    - All the methods in here are called from the RPC client.
    - If a RPC call does not have a corresponding method here, an exceptions
      will be thrown.
    - Arguments to these calls are added dynamically and will be treated as
      keyword arguments by the RPC client.
    '''

    def __init__(self, host, topic, manager=None):

        super(EngineService, self).__init__()
        self.host = cfg.CONF.host
        self.rpc_api_version = consts.RPC_API_VERSION
        self.topic = consts.TOPIC_KB_ENGINE
        # The following are initialized here, but assigned in start() which
        # happens after the fork when spawning multiple worker processes
        self.engine_id = None
        self.TG = None
        self.periodic_enable = cfg.CONF.scheduler.periodic_enable
        self.periodic_interval = cfg.CONF.scheduler.periodic_interval
        self.target = None
        self._rpc_server = None
        self.qm = None

    def init_tgm(self):
        self.TG = scheduler.ThreadGroupManager()

    def init_qm(self):
        self.qm = QuotaManager()

    def start(self):
        self.engine_id = str(uuid.uuid4())
        self.init_tgm()
        self.init_qm()
        target = oslo_messaging.Target(version=self.rpc_api_version,
                                       server=self.host,
                                       topic=self.topic)
        self.target = target
        self._rpc_server = rpc_messaging.get_rpc_server(self.target, self)
        self._rpc_server.start()

        super(EngineService, self).start()
        if self.periodic_enable:
            LOG.info("Adding periodic tasks for the engine to perform")
            self.TG.add_timer(self.periodic_interval,
                              self.periodic_balance_all, None, self.engine_id)

    def periodic_balance_all(self, engine_id):
        # Automated Quota Sync for all the keystone projects
        LOG.info(_LI("Periodic quota sync job started at: %s"),
                 time.strftime("%c"))
        self.qm.periodic_balance_all(engine_id)

    @request_context
    def get_total_usage_for_tenant(self, context, project_id):
        # Returns a dictionary containing nova, neutron &
        # cinder usages for the project
        LOG.info(_LI("Get total tenant usage called for: %s"),
                 project_id)
        return self.qm.get_total_usage_for_tenant(project_id)

    @request_context
    def quota_sync_for_project(self, context, project_id):
        # On Demand Quota Sync for a project, will be triggered by KB-API
        LOG.info(_LI("On Demand Quota Sync Called for: %s"),
                 project_id)
        self.qm.quota_sync_for_project(project_id)

    def _stop_rpc_server(self):
        # Stop RPC connection to prevent new requests
        LOG.debug(_("Attempting to stop engine service..."))
        try:
            self._rpc_server.stop()
            self._rpc_server.wait()
            LOG.info(_LI('Engine service stopped successfully'))
        except Exception as ex:
            LOG.error(_LE('Failed to stop engine service: %s'),
                      six.text_type(ex))

    def stop(self):
        self._stop_rpc_server()

        self.TG.stop()
        # Terminate the engine process
        LOG.info(_LI("All threads were gone, terminating engine"))
        super(EngineService, self).stop()
