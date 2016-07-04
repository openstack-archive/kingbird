# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import eventlet

from oslo_config import cfg
import oslo_messaging
from oslo_serialization import jsonutils

from kingbird.common import context

TRANSPORT = None
NOTIFIER = None

_ALIASES = {
    'kingbird.openstack.common.rpc.impl_kombu': 'rabbit',
    'kingbird.openstack.common.rpc.impl_qpid': 'qpid',
    'kingbird.openstack.common.rpc.impl_zmq': 'zmq',
}


class RequestContextSerializer(oslo_messaging.Serializer):
    def __init__(self, base):
        self._base = base

    def serialize_entity(self, ctxt, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(ctxt, entity)

    def deserialize_entity(self, ctxt, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(ctxt, entity)

    @staticmethod
    def serialize_context(ctxt):
        return ctxt.to_dict()

    @staticmethod
    def deserialize_context(ctxt):
        return context.RequestContext.from_dict(ctxt)


class JsonPayloadSerializer(oslo_messaging.NoOpSerializer):
    @classmethod
    def serialize_entity(cls, context, entity):
        return jsonutils.to_primitive(entity, convert_instances=True)


def setup(url=None, optional=False):
    """Initialise the oslo_messaging layer."""
    global TRANSPORT, NOTIFIER

    if url and url.startswith("fake://"):
        # NOTE: oslo_messaging fake driver uses time.sleep
        # for task switch, so we need to monkey_patch it
        eventlet.monkey_patch(time=True)

    if not TRANSPORT:
        oslo_messaging.set_transport_defaults('kingbird')
        exmods = ['kingbird.common.exception']
        try:
            TRANSPORT = oslo_messaging.get_transport(
                cfg.CONF, url, allowed_remote_exmods=exmods, aliases=_ALIASES)
        except oslo_messaging.InvalidTransportURL as e:
            TRANSPORT = None
            if not optional or e.url:
                raise

    if not NOTIFIER and TRANSPORT:
        serializer = RequestContextSerializer(JsonPayloadSerializer())
        NOTIFIER = oslo_messaging.Notifier(TRANSPORT, serializer=serializer)


def cleanup():
    """Cleanup the oslo_messaging layer."""
    global TRANSPORT, NOTIFIER
    if TRANSPORT:
        TRANSPORT.cleanup()
        TRANSPORT = NOTIFIER = None


def get_rpc_server(target, endpoint):
    """Return a configured oslo_messaging rpc server."""
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    return oslo_messaging.get_rpc_server(TRANSPORT, target, [endpoint],
                                         executor='eventlet',
                                         serializer=serializer)


def get_rpc_client(**kwargs):
    """Return a configured oslo_messaging RPCClient."""
    target = oslo_messaging.Target(**kwargs)
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    return oslo_messaging.RPCClient(TRANSPORT, target,
                                    serializer=serializer)


def get_notifier(publisher_id):
    """Return a configured oslo_messaging notifier."""
    return NOTIFIER.prepare(publisher_id=publisher_id)
