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

'''
Client side of the Kingbird RPC API.
'''

from oslo_config import cfg
from oslo_log import log as logging

from kingbird.common import config
from kingbird.common import consts
from kingbird.common import messaging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
config.register_options()


class EngineClient(object):
    """Client side of the kingbird engine rpc API.

    Version History:
     1.0 - Initial version (Mitaka 1.0 release)
    """

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self):
        self._client = messaging.get_rpc_client(
            topic=consts.TOPIC_KB_ENGINE,
            server=CONF.host,
            version=self.BASE_RPC_API_VERSION)

    @staticmethod
    def make_msg(method, **kwargs):
        return method, kwargs

    def call(self, ctxt, msg, version=None):
        method, kwargs = msg
        if version is not None:
            client = self._client.prepare(version=version)
        else:
            client = self._client
        return client.call(ctxt, method, **kwargs)

    def cast(self, ctxt, msg, version=None):
        method, kwargs = msg
        if version is not None:
            client = self._client.prepare(version=version)
        else:
            client = self._client
        return client.cast(ctxt, method, **kwargs)

    def get_total_usage_for_tenant(self, ctxt, project_id):
        return self.call(ctxt, self.make_msg('get_total_usage_for_tenant',
                                             project_id=project_id))

    def quota_sync_for_project(self, ctxt, project_id):
        return self.cast(ctxt, self.make_msg('quota_sync_for_project',
                                             project_id=project_id))

    def keypair_sync_for_user(self, ctxt, job_id, payload):
        return self.cast(
            ctxt,
            self.make_msg('keypair_sync_for_user', job_id=job_id,
                          payload=payload))

    def image_sync(self, ctxt, job_id, payload):
        return self.cast(
            ctxt,
            self.make_msg('image_sync', job_id=job_id, payload=payload))
