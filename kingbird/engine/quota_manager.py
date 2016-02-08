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

from kingbird.common.i18n import _
from kingbird.common.i18n import _LI
from kingbird.common import manager

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class QuotaManager(manager.Manager):
    """Manages tasks related to quota management."""

    def __init__(self, *args, **kwargs):
        LOG.debug(_('QuotaManager initialization...'))

        super(QuotaManager, self).__init__(service_name="quota_manager",
                                           *args, **kwargs)

    def periodic_balance_all(self, ctx):
        # TODO(Ashish): Implement Quota Syncing
        LOG.info(_LI("periodically balance quota for all keystone tenants"))
        pass
