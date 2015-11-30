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
from pecan import expose
from pecan import request
from pecan import rest

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
    def put(self):
        context = restcomm.extract_context_from_environ()

        payload = '## put call ##, request.body = '
        payload = payload + request.body
        return self.jd_api.say_hello_world_call(context, payload)

    @index.when(method='POST', template='json')
    def post(self):
        context = restcomm.extract_context_from_environ()

        payload = '## post call ##, request.body = '
        payload = payload + request.body
        return self.jd_api.say_hello_world_call(context, payload)

    @index.when(method='delete', template='json')
    def delete(self):

        # no return value to browser indeed for cast. check the log info in
        # jdmanager, jwmanager instead
        context = restcomm.extract_context_from_environ()

        payload = '## delete cast ##, request.body is null'
        payload = payload + request.body
        self.jd_api.say_hello_world_cast(context, payload)

        return self._delete_response(context)

    def _delete_response(self, context):

        context = context

        return {'cast example': 'check the log produced by jobdaemon '
                                + 'and jobworker, no value returned here'}
