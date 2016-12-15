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

import threading

from oslo_log import log as logging

from kingbird.common import context
from kingbird.common.i18n import _LI
from kingbird.common import manager
from kingbird.drivers.openstack import sdk

LOG = logging.getLogger(__name__)


class ResourceManager(manager.Manager):
    """Manages tasks related to resource management"""

    def __init__(self, *args, **kwargs):
        super(ResourceManager, self).__init__(service_name="resource_manager",
                                              *args, **kwargs)
        self.context = context.get_admin_context()

    def create_keypair(self, force, region, keypair, user_id):
        os_client = sdk.OpenStackDriver(region)
        os_client.create_keypairs(force, keypair, user_id)

    def resource_sync_for_user(self, payload, user_id, resource_identifier):
        if payload['resource_type'] == 'keypair':
            LOG.info(_LI("Keypair sync Called for user: %s"),
                     user_id)
            regions_thread_list = []
            target_regions = payload['target']
            force = payload['force']
            source_os_client = sdk.OpenStackDriver(payload['source'])
            source_keypair = source_os_client.get_keypairs(user_id,
                                                           resource_identifier)
            for region in target_regions:
                thread = threading.Thread(target=self.create_keypair,
                                          args=(force, region, source_keypair,
                                                user_id,))
                regions_thread_list.append(thread)
                thread.start()

            for region_thread in regions_thread_list:
                region_thread.join()
