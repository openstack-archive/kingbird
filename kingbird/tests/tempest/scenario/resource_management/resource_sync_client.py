# Copyright (c) 2017 Ericsson AB.
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

from kingbirdclient.api.v1 import client as kb_client

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client
from novaclient import client as nv_client
from oslo_log import log as logging
from tempest import config

CONF = config.CONF
NOVA_API_VERSION = "2.37"
KEYPAIRS = ["kb_test_keypair1", "kb_test_keypair2"]
resource_sync_url = "/os-sync/"
KINGBIRD_URL = CONF.kingbird.endpoint_url + CONF.kingbird.api_version

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


def get_openstack_drivers(keystone_client, region, project_name,
                          user_name, password):
    resources = dict()
    # Create Project, User and assign role to new user
    project = keystone_client.projects.create(project_name,
                                              CONF.auth.admin_domain_name)
    user = keystone_client.users.create(user_name, CONF.auth.admin_domain_name,
                                        project.id, password)
    sess = get_current_session(user_name, password, project_name)
    # Create new client to form session
    new_key_client = ks_client.Client(session=sess)
    # Create member role to which we create keypair and Sync
    mem_role = [current_role.id for current_role in
                keystone_client.roles.list()
                if current_role.name == 'Member'][0]
    keystone_client.roles.grant(mem_role, user=user, project=project)
    token = new_key_client.session.get_token()
    nova_client = nv_client.Client(NOVA_API_VERSION,
                                   session=sess,
                                   region_name=region)
    kingbird_client = kb_client.Client(kingbird_url=KINGBIRD_URL,
                                       auth_token=token,
                                       project_id=project.id)
    resources = {"user_id": user.id, "project_id": project.id,
                 "session": sess, "token": token,
                 "nova_version": NOVA_API_VERSION,
                 "keypairs": KEYPAIRS,
                 "os_drivers": {'keystone': keystone_client,
                                'nova': nova_client,
                                'kingbird': kingbird_client}}

    return resources


def get_keystone_client(session):
    return ks_client.Client(session=session)


def sync_resource(openstack_drivers, post_body):
    kb = openstack_drivers['kingbird']
    response = kb.sync_manager.sync_resources(**post_body)
    result = dict()
    for i in response:
        result['id'] = i.id
        result['status'] = i.status
        result['created_at'] = i.created_at
    res = dict()
    res['job_status'] = result
    return res


def get_sync_job_list(openstack_drivers, action):
    kb = openstack_drivers['kingbird']
    response = kb.sync_manager.list_sync_jobs(action)
    result = dict()
    job_set = list()
    res = dict()
    for i in response:
        result['id'] = i.id
        result['sync_status'] = i.status
        result['created_at'] = i.created_at
        result['updated_at'] = i.updated_at
        job_set.append(result.copy())
    res['job_set'] = job_set
    return res


def get_sync_job_detail(openstack_drivers, job_id):
    kb = openstack_drivers['kingbird']
    response = kb.sync_manager.sync_job_detail(job_id)
    result = dict()
    job_set = list()
    res = dict()
    for i in response:
        result['resource'] = i.resource_name
        result['target_region'] = i.target_region
        result['sync_status'] = i.status
        result['created_at'] = i.created_at
        result['updated_at'] = i.updated_at
        result['source_region'] = i.source_region
        result['resource_type'] = i.resource_type
        job_set.append(result.copy())
    res['job_set'] = job_set
    return res


def delete_db_entries(openstack_drivers, job_id):
    kb = openstack_drivers['kingbird']
    kb.sync_manager.delete_sync_job(job_id)


def get_regions(key_client):
    return [current_region.id for current_region in
            key_client.regions.list()]


def cleanup_resources(openstack_drivers, resource_ids):
    keystone_client = openstack_drivers['keystone']
    keystone_client.projects.delete(resource_ids['project_id'])
    keystone_client.users.delete(resource_ids['user_id'])


def cleanup_keypairs(regions, resource_ids,
                     current_sess):
    for current_region in regions:
        for keypair in KEYPAIRS:
            nova_client = nv_client.Client(NOVA_API_VERSION,
                                           session=current_sess,
                                           region_name=current_region)
            nova_client.keypairs.delete(keypair,
                                        user_id=resource_ids['user_id'])


def create_keypairs(openstack_drivers):
    nova_client = openstack_drivers['nova']
    resources = dict()
    for keypair in KEYPAIRS:
        resources[keypair] = nova_client.keypairs.create(keypair)
    return resources
