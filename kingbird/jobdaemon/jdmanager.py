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
import oslo_messaging as messaging

from kingbird.common.i18n import _
from kingbird.common.i18n import _LI
from kingbird.common import manager
# from kingbird.jobworker import jwrpcapi

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class JDManager(manager.Manager):
    """Manages the running job from creation to destruction."""

    target = messaging.Target(version='1.0')

    def __init__(self, *args, **kwargs):
        LOG.debug(_('JDManager initialization...'))

        super(JDManager, self).__init__(service_name="job_daemon",
                                        *args, **kwargs)

        # self.jw_api = jwrpcapi.JobWorkerAPI()

    def init_host(self):
        LOG.debug(_('JDManager init_host...'))

        pass

    def cleanup_host(self):
        LOG.debug(_('JDManager cleanup_host...'))

        pass

    def pre_start_hook(self):
        LOG.debug(_('JDManager pre_start_hook...'))

        pass

    def post_start_hook(self):
        LOG.debug(_('JDManager post_start_hook...'))

        pass

    # rpc message endpoint handling
    def say_hello_world_call(self, ctx, payload):

        LOG.info(_LI("jobdaemon say hello world, call payload: %s"), payload)

        # self.jw_api.say_hello_world_call(ctx, 'hello from jobdaemon')

        info_text = "payload: %s" % payload
        return {'jobdaemon': info_text}

    def say_hello_world_cast(self, ctx, payload):

        LOG.info(_LI("jobdaemon say hello world, cast payload: %s"), payload)

        # self.jw_api.say_hello_world_cast(ctx, 'hello from jobdaemon')

        info_text = "payload: %s" % payload
        return {'jobdaemon': info_text}
