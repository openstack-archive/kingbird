# Copyright (c) 2016 Ericsson AB.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import json
import requests

from oslo_log import log as logging
from tempest import config

CONF = config.CONF

LOG = logging.getLogger(__name__)


def get_keystone_authtoken():
    headers = {
        'Content-type': 'application/json',
    }
    data = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                    ],
                "password": {
                    "user": {
                        "domain": {
                            "name": CONF.auth.admin_domain_name
                            },
                        "name": CONF.auth.admin_username,
                        "password": CONF.auth.admin_password
                        }
                    }
                },
            "scope": {
                "project": {
                    "domain": {
                        "name": CONF.auth.admin_domain_name
                        },
                    "name": CONF.auth.admin_tenant_name
                    }
                }
            }
    }
    url_string = CONF.identity.uri_v3 + "/auth/tokens"
    body = json.dumps(data)
    response = requests.post(url_string, headers=headers, data=body)
    token = response.headers['X-Subject-Token']
    return token


def get_urlstring_and_headers(token):
    admin_tenant_id = CONF.auth.admin_tenant_name
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token,
        'X-ROLE': 'admin',
    }
    url_string = CONF.kingbird.endpoint_url + CONF.kingbird.api_version + \
        "/" + admin_tenant_id + "/os-quota-sets/"
    return headers, url_string


def create_custom_kingbird_quota(token, project_id, new_quota_values):
    body = json.dumps(new_quota_values)
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + project_id
    response = requests.put(url_string, headers=headers, data=body)
    return response.text


def get_custom_kingbird_quota(token, project_id):
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + project_id
    response = requests.get(url_string, headers=headers)
    return response.text


def delete_custom_kingbird_quota(token, project_id, quota_to_delete=None):
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + project_id
    if quota_to_delete:
        body = json.dumps(quota_to_delete)
        response = requests.delete(url_string, headers=headers, data=body)
    else:
        response = requests.delete(url_string, headers=headers)
    return response.text


def get_default_kingbird_quota(token):
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + "defaults"
    response = requests.get(url_string, headers=headers)
    return response.text


def quota_sync_for_project(token, project_id):
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + project_id + "/sync"
    response = requests.put(url_string, headers=headers)
    return response.text


def get_quota_usage_for_project(token, project_id):
    headers, url_string = get_urlstring_and_headers(token)
    url_string = url_string + project_id + "/detail"
    response = requests.get(url_string, headers=headers)
    return response.text


def create_custom_kingbird_quota_wrong_token(token,
                                             project_id, new_quota_values):
    headers, url_string = get_urlstring_and_headers(token)
    headers['X-Auth-Token'] = 'fake_token'
    url_string = url_string + project_id
    body = json.dumps(new_quota_values)
    response = requests.put(url_string, headers=headers, data=body)
    return response
