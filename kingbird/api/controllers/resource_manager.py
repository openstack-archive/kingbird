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
import pecan
from pecan import expose
from pecan import request

import restcomm
import threading

from kingbird.common.i18n import _
from kingbird.drivers.openstack import sdk
from kingbird.rpc import client as rpc_client

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


class ResourceManagerController(object):
    VERSION_ALIASES = {
        'mitaka': '1.0',
    }

    def __init__(self, *args, **kwargs):
        super(ResourceManagerController, self).__init__(*args, **kwargs)
        self.rpc_client = rpc_client.EngineClient()

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    def _check_keypair_in_region(self, region, user_id,
                                 source_keypair,
                                 overlapped_resources):
        target_os_client = sdk.OpenStackDriver(region)
        if source_keypair == target_os_client.get_keypairs(user_id,
                                                           source_keypair):

            overlapped_resources[region] = source_keypair.name

    @index.when(method='POST', template='json')
    def post(self, user_id):
        regions_thread = []
        overlapped_resources = {}
        context = restcomm.extract_context_from_environ()
        if not request.body:
            pecan.abort(400, _('Body required'))
        payload = eval(request.body)
        payload = payload.get('resource_set')
        if not payload:
            pecan.abort(400, _('resource_set required'))

        # Retrieve regions to which keypairs have to be synced
        target_regions = payload.get('target')
        source_regions = payload.get('source')

        if not target_regions:
            pecan.abort(400, _('Target regions required'))

        if not source_regions:
            pecan.abort(400, _('Source regions required'))

        source_key_name = payload['resources']
        # Create Source_Region_object
        source_os_client = sdk.OpenStackDriver(payload['source'])
        force = eval(str(payload['force']))
        if payload['resource_type'] == 'keypair':
            source_keypair = source_os_client.get_keypairs(user_id,
                                                           source_key_name)
            if not source_keypair:
                pecan.abort(404)

            for region in target_regions:
                thread = threading.Thread(target=self._check_keypair_in_region,
                                          args=(region,
                                                user_id, source_keypair,
                                                overlapped_resources,))
                regions_thread.append(thread)
                thread.start()

            # Wait for all the threads to create keypairs in region
            for region_thread in regions_thread:
                region_thread.join()
            if not force and overlapped_resources:
                for region in overlapped_resources:
                    message = region + " already has " + \
                        overlapped_resources[region]
                pecan.abort(409, message)
        else:
            pecan.abort(400, _('Bad resource_type'))

        return self._sync(user_id, payload, context, source_key_name)

    def _sync(self, user_id, payload, context, resource_identifier):
        self.rpc_client.resource_sync_for_user(context, payload,
                                               user_id, resource_identifier)
        return payload['resource_type'] + " synced for user " + user_id
