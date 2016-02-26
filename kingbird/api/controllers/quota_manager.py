# Copyright (c) 2016 Ericsson AB
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

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import pecan
from pecan import expose
from pecan import request
from pecan import rest

import restcomm

from kingbird.common import rpc
from kingbird.common.serializer import KingbirdSerializer as Serializer
from kingbird.common import topics

CONF = cfg.CONF

rpc_api_cap_opt = cfg.StrOpt('kb-engine',
                             help='Set a version cap for messages sent to'
                                  'kb-engine services. If you plan to do a'
                                  'live upgrade from an old version to a'
                                  'newer version, you should set this option'
                                  'to the old version before beginning the'
                                  'live upgrade procedure. Only upgrading'
                                  'to the next version is supported, so you'
                                  'cannot skip a release for the live upgrade'
                                  'procedure.')
CONF.register_opt(rpc_api_cap_opt, 'upgrade_levels')

LOG = logging.getLogger(__name__)


class QuotaManagerController(rest.RestController):
    VERSION_ALIASES = {
        'mitaka': '1.0',
    }

    def __init__(self, *args, **kwargs):
        super(QuotaManagerController, self).__init__(*args, **kwargs)
        target = messaging.Target(topic=topics.TOPIC_KB_ENGINE, version='1.0')
        upgrade_level = CONF.upgrade_levels.kb_engine
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

    @expose(generic=True, template='json')
    def index(self, arg=None):
        if pecan.request.method != 'GET':
            pecan.abort(405)

        context = restcomm.extract_context_from_environ()
        if context.is_admin:
            return {'Admin call for index with project': arg}
        else:
            return {'Non admin call for index with project': arg}

    @index.when(method='PUT', template='json')
    def put(self):
        context = restcomm.extract_context_from_environ()

        payload = '## put call ##, request.body = '
        payload = payload + request.body
        # To illustrate RPC, below line is written. Will be replaced by
        # DB API call for updating quota limits for a tenant
        return self.client.call(context, 'say_hello_world_call',
                                payload=payload)

    @index.when(method='POST', template='json')
    def post(self):
        context = restcomm.extract_context_from_environ()

        payload = '## post call ##, request.body = '
        payload = payload + request.body
        # To illustrate RPC, below line is written. Will be replaced by
        # DB API call for creating quota limits for a tenant
        return self.client.call(context, 'say_hello_world_call',
                                payload=payload)

    @index.when(method='delete', template='json')
    def delete(self):
        context = restcomm.extract_context_from_environ()

        payload = '## delete cast ##, request.body is null'
        payload = payload + request.body
        # To illustrate RPC, below line is written. Will be replaced by
        # DB API call for deleting quota limits for a tenant
        self.client.cast(context, 'say_hello_world_cast', payload=payload)
        return self._delete_response(context)

    def _delete_response(self, context):
        context = context
        return {'cast example': 'check the log produced by engine'
                                + 'and no value returned here'}


def list_opts():
    yield None, rpc_api_cap_opt
