#
# Copyright 2013 Red Hat, Inc.
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
#
#    copy and modify from OpenStack Nova

"""Base RPC client and server common to all services."""

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_serialization import jsonutils

from kingbird.common import rpc

CONF = cfg.CONF
rpc_api_cap_opt = [
    cfg.StrOpt('base_client_api',
               help='Set a version cap for messages sent to the'
               'base api in any service')
]

rpc_api_group = cfg.OptGroup('rpc_api_options')
cfg.CONF.register_group(rpc_api_group)
cfg.CONF.register_opts(rpc_api_cap_opt, group=rpc_api_group)

_NAMESPACE = 'base_client_api'


class BaseClientAPI(object):
    """Client side of the base rpc API.

    API version history:
        1.0 - Initial version.
    """

    VERSION_ALIASES = {
        # baseapi was added in the first version of Kingbird
    }

    def __init__(self, topic):
        """Init method for BaseClientApi Class."""
        super(BaseClientAPI, self).__init__()
        target = messaging.Target(topic=topic,
                                  namespace=_NAMESPACE,
                                  version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.rpc_api_options.baseapi,
                                               CONF.rpc_api_options.baseapi)
        self.client = rpc.get_client(target, version_cap=version_cap)

    def ping(self, context, arg, timeout=None):
        arg_p = jsonutils.to_primitive(arg)
        cctxt = self.client.prepare(timeout=timeout)
        return cctxt.call(context, 'ping', arg=arg_p)


class BaseServerRPCAPI(object):
    """Server side of the base RPC API."""

    target = messaging.Target(namespace=_NAMESPACE, version='1.0')

    def __init__(self, service_name):
        self.service_name = service_name

    def ping(self, context, arg):
        resp = {'service': self.service_name, 'arg': arg}
        return jsonutils.to_primitive(resp)


def list_opts():
    yield rpc_api_group.name, rpc_api_cap_opt
