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

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client
from novaclient import client as nv_client
from oslo_log import log as logging
from tempest import config

CONF = config.CONF
NOVA_API_VERSION = "2.37"
KEYPAIR_NAME = "kb_test_keypair"
resource_sync_url = "/os-sync/"

LOG = logging.getLogger(__name__)


def get_session():
    return get_current_session(
        CONF.auth.admin_username,
        CONF.auth.admin_password,
        CONF.auth.admin_project_name
        )


def get_current_session(username, password, tenant_name):
    auth = v3.Password(
        auth_url=CONF.identity.uri_v3,
        username=username,
        password=password,
        project_name=tenant_name,
        user_domain_name=CONF.auth.admin_domain_name,
        project_domain_name=CONF.auth.admin_domain_name)
    sess = session.Session(auth=auth)
    return sess


def get_openstack_drivers(key_client, region, project_name,
                          user_name, password):
    # Create Project, User and assign role to new user
    project = key_client.projects.create(project_name,
                                         CONF.auth.admin_domain_name)
    user = key_client.users.create(user_name, CONF.auth.admin_domain_name,
                                   project.id, password)
    admin_role = [current_role.id for current_role in
                  key_client.roles.list() if current_role.name == 'admin'][0]
    key_client.roles.grant(admin_role, user=user, project=project)
    session = get_current_session(user_name, password, project_name)
    nova_client = nv_client.Client(NOVA_API_VERSION,
                                   session=session,
                                   region_name=region)
    return {"user_id": user.id, "project_id": project.id, "session": session,
            "os_drivers": [key_client, nova_client]}


def get_key_client(session):
    return ks_client.Client(session=session)


def get_urlstring_and_headers(token, api_url):
    admin_tenant_id = CONF.auth.admin_project_name
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token,
        'X-ROLE': 'admin',
    }
    url_string = CONF.kingbird.endpoint_url + CONF.kingbird.api_version + \
        "/" + admin_tenant_id + api_url

    return headers, url_string


def get_keypair_sync_url_and_headers(token, api_url):
    admin_user_id = CONF.auth.admin_username
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token,
        'X-ROLE': 'admin',
    }
    url_string = CONF.kingbird.endpoint_url + CONF.kingbird.api_version + \
        "/" + admin_user_id + api_url

    return headers, url_string


def sync_keypair(token, user_id, post_body):
    body = json.dumps(post_body)
    headers, url_string = get_keypair_sync_url_and_headers(token,
                                                           resource_sync_url)
    url_string = url_string + user_id
    response = requests.post(url_string, headers=headers, data=body)
    return response.status_code


def get_regions(key_client):
    return [current_region.id for current_region in
            key_client.regions.list()]


def resource_cleanup(openstack_drivers, regions, resource_ids, current_sess):
    key_client = openstack_drivers[0]
    for current_region in regions:
        nova_client = nv_client.Client(NOVA_API_VERSION,
                                       session=current_sess,
                                       region_name=current_region)
        nova_client.keypairs.delete(KEYPAIR_NAME,
                                    user_id=resource_ids['user_id'])
    key_client.projects.delete(resource_ids['project_id'])
    key_client.users.delete(resource_ids['user_id'])


def create_resources(openstack_drivers):
    nova_client = openstack_drivers[1]
    keypair = nova_client.keypairs.create(KEYPAIR_NAME)
    return {'keypair': keypair.name}
