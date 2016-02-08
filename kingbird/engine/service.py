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
from oslo_service import service as srv

from kingbird.common.i18n import _
from kingbird.common.serializer import KingbirdSerializer as Serializer
from kingbird.common.service import Service
from kingbird.common import topics
from kingbird.engine.listener import EngineManager

_TIMER_INTERVAL = 30
_TIMER_INTERVAL_MAX = 60

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

host_opts = [
    cfg.StrOpt('host',
               default='localhost',
               help='hostname of the machine')
]

host_opt_group = cfg.OptGroup('host_details')
cfg.CONF.register_group(host_opt_group)
cfg.CONF.register_opts(host_opts, group=host_opt_group)


class EngineService(Service):
    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, serializer=None,
                 *args, **kwargs):
        super(EngineService, self).__init__(host, binary, topic, manager,
                                            report_interval, periodic_enable,
                                            periodic_fuzzy_delay,
                                            periodic_interval_max, serializer,
                                            *args, **kwargs)


def create_service():

    LOG.debug(_('create KB engine service'))

    engine_manager = EngineManager()
    engine_service = EngineService(
        host=cfg.CONF.host_details.host,
        binary="kb_engine",
        topic=topics.TOPIC_KB_ENGINE,
        manager=engine_manager,
        periodic_enable=True,
        report_interval=_TIMER_INTERVAL,
        periodic_interval_max=_TIMER_INTERVAL_MAX,
        serializer=Serializer()
    )

    engine_service.start()

    return engine_service


_launcher = None


def serve(engine_service, workers=1):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = srv.launch(CONF, engine_service, workers=workers)


def wait():
    _launcher.wait()
