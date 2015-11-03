# Copyright 2015 Huawei Technologies Co., Ltd.
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
from kingbird.jobdaemon.jdmanager import JDManager

_TIMER_INTERVAL = 30
_TIMER_INTERVAL_MAX = 60

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class JDService(Service):
    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, serializer = None,
                 *args, **kwargs):
        super(JDService, self).__init__(host, binary, topic, manager,
                                        report_interval, periodic_enable,
                                        periodic_fuzzy_delay,
                                        periodic_interval_max, serializer,
                                        *args, **kwargs)


def create_service():

    LOG.debug(_('create job daemon server'))

    jdmanager = JDManager()
    jdservice = JDService(
        host=CONF.host,
        binary="job_daemon",
        topic=topics.TOPIC_JOBDAEMON,
        manager=jdmanager,
        periodic_enable=True,
        report_interval=_TIMER_INTERVAL,
        periodic_interval_max=_TIMER_INTERVAL_MAX,
        serializer=Serializer()
    )

    jdservice.start()

    return jdservice


_launcher = None


def serve(jdservice, workers=1):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = srv.launch(CONF, jdservice, workers=workers)


def wait():
    _launcher.wait()
