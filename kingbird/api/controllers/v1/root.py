# Copyright (c) 2017 Ericsson AB.
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


import pecan

from kingbird.api.controllers.v1 import quota_class
from kingbird.api.controllers.v1 import quota_manager
from kingbird.api.controllers.v1 import sync_manager


class Controller(object):

    def _get_resource_controller(self, tenant_id, remainder):
        if not remainder:
            pecan.abort(404)
            return
        minor_version = remainder[-1]
        remainder = remainder[:-1]
        sub_controllers = dict()
        if minor_version == '0':
            sub_controllers["os-quota-sets"] = quota_manager.\
                QuotaManagerController
            sub_controllers["os-quota-class-sets"] = quota_class.\
                QuotaClassSetController
            sub_controllers["os-sync"] = sync_manager.\
                ResourceSyncController

        elif minor_version == '1':
            sub_controllers["os-quota-sets"] = quota_manager.\
                QuotaManagerV1Controller

        for name, ctrl in sub_controllers.items():
            setattr(self, name, ctrl)

        resource = remainder[0]
        if resource not in sub_controllers:
            pecan.abort(404)
            return

        # Pass the tenant_id for verification
        remainder = (tenant_id,) + remainder[1:]
        return sub_controllers[resource](), remainder

    @pecan.expose()
    def _lookup(self, tenant_id, *remainder):
        return self._get_resource_controller(tenant_id, remainder)
