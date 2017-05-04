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


from pecan import request

import kingbird.common.context as k_context


def extract_context_from_environ():
    context_paras = {'auth_token': 'HTTP_X_AUTH_TOKEN',
                     'user': 'HTTP_X_USER_ID',
                     'project': 'HTTP_X_TENANT_ID',
                     'user_name': 'HTTP_X_USER_NAME',
                     'tenant_name': 'HTTP_X_PROJECT_NAME',
                     'domain': 'HTTP_X_DOMAIN_ID',
                     'roles': 'HTTP_X_ROLE',
                     'user_domain': 'HTTP_X_USER_DOMAIN_ID',
                     'project_domain': 'HTTP_X_PROJECT_DOMAIN_ID',
                     'request_id': 'openstack.request_id'}

    environ = request.environ

    for key in context_paras:
        context_paras[key] = environ.get(context_paras[key])
    role = environ.get('HTTP_X_ROLE')

    context_paras['is_admin'] = role == 'admin'
    return k_context.RequestContext(**context_paras)
