# Copyright (c) 2015 Huawei Tech. Co., Ltd.
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

from kingbird.api.controllers import quota_manager
from kingbird.api.controllers.v1 import quota_class


class RootController(object):

    @pecan.expose('json')
    def _lookup(self, version, *remainder):
        if version == 'v1.0':
            return V1Controller(), remainder

    @pecan.expose(generic=True, template='json')
    def index(self):
        return {
            "versions": [
                {
                    "status": "CURRENT",
                    "links": [
                        {
                            "rel": "self",
                            "href": pecan.request.application_url + "/v1.0/"
                            }
                        ],
                    "id": "v1.0",
                    "updated": "2016-03-07"
                    }
                ]
            }

    @index.when(method='POST')
    @index.when(method='PUT')
    @index.when(method='DELETE')
    @index.when(method='HEAD')
    @index.when(method='PATCH')
    def not_supported(self):
        pecan.abort(405)


class V1Controller(object):

    def __init__(self):

        self.sub_controllers = {
            "os-quota-sets": quota_manager.QuotaManagerController,
            "os-quota-class-sets": quota_class.QuotaClassSetController,
        }

        for name, ctrl in self.sub_controllers.items():
            setattr(self, name, ctrl)

    def _get_resource_controller(self, tenant_id, remainder):
        if not remainder:
            pecan.abort(404)
            return
        resource = remainder[0]
        if resource not in self.sub_controllers:
            pecan.abort(404)
            return

        return self.sub_controllers[resource](), remainder[1:]

    @pecan.expose()
    def _lookup(self, tenant_id, *remainder):
        return self._get_resource_controller(tenant_id, remainder)

    @pecan.expose(generic=True, template='json')
    def index(self):
        return {
            "version": "1.0",
            "links": [
                {"rel": "self",
                 "href": pecan.request.application_url + "/v1.0"}
            ] + [
                {"rel": name,
                 "href": pecan.request.application_url +
                    "/v1.0/{tenant_id}/" + name}
                for name in sorted(self.sub_controllers)
            ]
        }

    @index.when(method='POST')
    @index.when(method='PUT')
    @index.when(method='DELETE')
    @index.when(method='HEAD')
    @index.when(method='PATCH')
    def not_supported(self):
        pecan.abort(405)
