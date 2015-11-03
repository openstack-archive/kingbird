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
from pecan import rest
from pecan import expose

import restcomm
from kingbird.jobdaemon import jdrpcapi


class HelloWorldController(rest.RestController):

    def __init__(self, *args, **kwargs):
        super(HelloWorldController, self).__init__(*args, **kwargs)
        self.jd_api = jdrpcapi.JobDaemonAPI()

    @expose(generic=True, template='json')
    def index(self):
        if pecan.request.method != 'GET':
            pecan.abort(405)

        context = restcomm.extract_context_from_environ()
        if context.is_admin:
            return {'hello world message for admin': 'GET'}
        else:
            return {'hello world message for non-admin': 'GET'}

    @index.when(method='PUT', template='json')
    def put(self, **kw):
        context = restcomm.extract_context_from_environ()
        return self.jd_api.say_hello_world_call(context,'## put call ##')

    @index.when(method='POST', template='json')
    def post(self, **kw):
        context = restcomm.extract_context_from_environ()
        return self.jd_api.say_hello_world_call(context,'## post call ##')

    @index.when(method='delete', template='json')
    def delete(self):
        context = restcomm.extract_context_from_environ()
        return self.jd_api.say_hello_world_cast(context,'## delete cast ##')