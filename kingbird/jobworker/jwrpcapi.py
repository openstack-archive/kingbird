# Copyright 2015 Huawei Technologies Co., Ltd.
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
Client side of the job worker RPC API.
"""

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from kingbird.common import rpc
from kingbird.common.serializer import KingbirdSerializer as Serializer
from kingbird.common import topics


CONF = cfg.CONF

rpcapi_cap_opt = cfg.StrOpt('jobworker',
        help='Set a version cap for messages sent to jobdaemon services. '
             'If you plan to do a live upgrade from an old version to a'
             'newer version, you should set this option to the old version'
             'before beginning the live upgrade procedure. Only upgrading'
             'to the next version is supported, so you cannot skip a release'
             'for the live upgrade procedure.')
CONF.register_opt(rpcapi_cap_opt, 'upgrade_levels')

LOG = logging.getLogger(__name__)


class JobWorkerAPI(object):
    '''Client side of the job worker rpc API.
    API version history:
        * 1.0 - Initial version.
    '''

    VERSION_ALIASES = {
        'mitaka': '1.0',
    }

    def __init__(self):
        super(JobWorkerAPI, self).__init__()
        target = messaging.Target(topic=topics.TOPIC_JOBWORKER, version='1.0')
        upgrade_level = CONF.upgrade_levels.jobworker
        version_cap = 1.0
        if upgrade_level == 'auto':
            version_cap = self._determine_version_cap(target)
        else:
            version_cap = self.VERSION_ALIASES.get(upgrade_level,
                                                   upgrade_level)
        serializer = Serializer()
        self.client = rpc.get_client(target,
                              version_cap=version_cap,
                              serializer=serializer)

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    def say_hello_world_call(self, ctxt, payload):
        call_context = self.client.prepare()
        return call_context.call(ctxt, 'say_hello_world_call', payload=payload)

    def say_hello_world_cast(self, ctxt, payload):
        call_context = self.client.prepare()
        return call_context.cast(ctxt, 'say_hello_world_cast', payload=payload)
