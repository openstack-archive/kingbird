#!/usr/bin/env python
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
Kingbird Engine Server.
"""

import eventlet
eventlet.monkey_patch()

from oslo_config import cfg
from oslo_i18n import _lazy
from oslo_log import log as logging
from oslo_service import service

from kingbird.common import config
from kingbird.common.i18n import _
from kingbird.common import messaging
from kingbird.common import topics

_lazy.enable_lazy()

common_opts = [
    cfg.StrOpt('host', default='kingbird.host',
               help=_("The host name for RPC server")),
    cfg.IntOpt('workers', default=1,
               help=_("number of workers")),
    cfg.StrOpt('state_path',
               default='/var/lib/kingbird',
               deprecated_name='pybasedir',
               help="Top-level directory for maintaining kingbird's state"),
]

cfg.CONF.register_opts(common_opts)
config.register_options()
LOG = logging.getLogger('kingbird.engine')


def main():
    logging.register_options(cfg.CONF)
    cfg.CONF(project='kingbird', prog='kingbird-engine')
    logging.setup(cfg.CONF, 'kingbird-engine')
    logging.set_defaults()
    messaging.setup()

    from kingbird.engine import service as engine

    srv = engine.EngineService(cfg.CONF.host_details.host,
                               topics.TOPIC_KB_ENGINE)
    launcher = service.launch(cfg.CONF,
                              srv, workers=cfg.CONF.workers)
    # the following periodic tasks are intended serve as HA checking
    # srv.create_periodic_tasks()
    launcher.wait()

if __name__ == '__main__':
    main()
