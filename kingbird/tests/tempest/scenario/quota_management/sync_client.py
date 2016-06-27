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

import collections
import json
import requests
import time

from cinderclient import client as ci_client
from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client
from neutronclient.neutron import client as nt_client
from novaclient import client as nv_client
from oslo_log import log as logging
from tempest import config

CONF = config.CONF
NOVA_API_VERSION = "2.1"
NEUTRON_API_VERSION = "2.0"
CINDER_API_VERSION = "2"
VOLUME_SIZE = 1
VOLUME_NAME = "kb_test_volume"
FLAVOR_NAME = "kb_test_flavor"
NETWORK_NAME = "kb_test_network"
SUBNET_NAME = "kb_test_subnet"
SERVER_NAME = "kb_test_server"
SUBNET_RANGE = "192.168.199.0/24"
quota_api_url = "/os-quota-sets/"
quota_class_api_url = "/os-quota-class-sets/"

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


def get_openstack_drivers(key_client, region, project_name, user_name,
                          password):
    # Create Project, User and asign role to new user
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
    neutron_client = nt_client.Client(NEUTRON_API_VERSION, session=session,
                                      region_name=region)
    cinder_client = ci_client.Client(CINDER_API_VERSION, session=session,
                                     region_name=region)
    return {"user_id": user.id, "project_id": project.id, "session": session,
            "os_drivers": [key_client, nova_client, neutron_client,
                           cinder_client]}


def get_key_client(session):
    return ks_client.Client(session=session)


def create_instance(openstack_drivers, resource_ids, count=1):
    nova_client = openstack_drivers[1]
    server_ids = []
    image = nova_client.images.find(id=CONF.compute.image_ref)
    flavor = nova_client.flavors.find(id=resource_ids['flavor_id'])
    try:
        for x in range(count):
            server = nova_client.servers.create(
                SERVER_NAME, image, flavor,
                nics=[{'net-id': resource_ids['network_id']}])
            server_ids.append(server.id)
        return server_ids
    except Exception as e:
        e.args = tuple(server_ids)
        raise e


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


def create_custom_kingbird_quota(token, project_id, new_quota_values):
    body = json.dumps(new_quota_values)
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + project_id
    response = requests.put(url_string, headers=headers, data=body)
    return response.text


def get_custom_kingbird_quota(token, project_id):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + project_id
    response = requests.get(url_string, headers=headers)
    return response.text


def delete_custom_kingbird_quota(token, project_id, quota_to_delete=None):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + project_id
    if quota_to_delete:
        body = json.dumps(quota_to_delete)
        response = requests.delete(url_string, headers=headers, data=body)
    else:
        response = requests.delete(url_string, headers=headers)
    return response.text


def get_default_kingbird_quota(token):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + "defaults"
    response = requests.get(url_string, headers=headers)
    return response.text


def quota_sync_for_project(token, project_id):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + project_id + "/sync"
    response = requests.put(url_string, headers=headers)
    return response.text


def get_quota_usage_for_project(token, project_id):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    url_string = url_string + project_id + "/detail"
    response = requests.get(url_string, headers=headers)
    return response.text


def create_custom_kingbird_quota_wrong_token(token,
                                             project_id, new_quota_values):
    headers, url_string = get_urlstring_and_headers(token, quota_api_url)
    headers['X-Auth-Token'] = 'fake_token'
    url_string = url_string + project_id
    body = json.dumps(new_quota_values)
    response = requests.put(url_string, headers=headers, data=body)
    return response


def get_regions(key_client):
    return [current_region.id for current_region in
            key_client.regions.list()]


def delete_resource_with_timeout(service_client, resource_ids, service_type):
    # Delete the resources based on service_type argument
    for resource_id in resource_ids:
        if service_type == 'nova':
            # Delete nova servers
            service_client.servers.delete(resource_id)
        elif service_type == 'cinder':
            # Delete cinder volumes
            service_client.volumes.delete(resource_id)
        else:
            LOG.exception('Invalid service type: %s' % service_type)
            return
    retries = 6
    # Delete may take time, So wait(with timeout) till the
    # resources are deleted
    while retries > 0:
        LOG.debug("waiting for resources to get deleted")
        time.sleep(1)
        if service_type == 'nova':
            resource_list = [current_server.id for current_server in
                             service_client.servers.list()]
        elif service_type == 'cinder':
            resource_list = [current_volume.id for current_volume in
                             service_client.volumes.list()]
        # Check if there is any resource left in resource list
        if len(set(resource_ids) & set(resource_list)):
            continue
        else:
            # Deleted all the resources
            return
    LOG.exception('Resource deleting failed, manually delete with IDs %s'
                  % resource_ids)


def delete_instance(openstack_drivers, resource_ids):
    delete_resource_with_timeout(
        openstack_drivers[1],
        resource_ids['server_ids'], 'nova')
    resource_ids['server_ids'] = []


def delete_volume(openstack_drivers, resource_ids):
    delete_resource_with_timeout(
        openstack_drivers[3],
        resource_ids['volume_ids'], 'cinder')
    resource_ids['volume_ids'] = []


def resource_cleanup(openstack_drivers, resource_ids):
    key_client = openstack_drivers[0]
    nova_client = openstack_drivers[1]
    neutron_client = openstack_drivers[2]
    delete_instance(openstack_drivers, resource_ids)
    delete_volume(openstack_drivers, resource_ids)
    nova_client.flavors.delete(resource_ids['flavor_id'])
    neutron_client.delete_subnet(resource_ids['subnet_id'])
    neutron_client.delete_network(resource_ids['network_id'])
    key_client.projects.delete(resource_ids['project_id'])
    key_client.users.delete(resource_ids['user_id'])


def get_usage_from_os_client(session, regions, project_id):
    resource_usage_all = collections.defaultdict(dict)
    neutron_opts = {'tenant_id': project_id}
    cinder_opts = {'all_tenants': 1, 'project_id': project_id}
    for current_region in regions:
        resource_usage = collections.defaultdict(dict)
        nova_client = nv_client.Client(NOVA_API_VERSION,
                                       session=session,
                                       region_name=current_region)
        neutron_client = nt_client.Client(NEUTRON_API_VERSION,
                                          session=session,
                                          region_name=current_region)
        cinder_client = ci_client.Client(CINDER_API_VERSION,
                                         session=session,
                                         region_name=current_region)
        limits = nova_client.limits.get().to_dict()
        # Read nova usages
        resource_usage['ram'] = limits['absolute']['totalRAMUsed']
        resource_usage['cores'] = limits['absolute']['totalCoresUsed']
        resource_usage['instances'] = limits['absolute']['totalInstancesUsed']
        resource_usage['key_pairs'] = len(nova_client.keypairs.list())
        # Read neutron usages
        resource_usage['network'] = len(neutron_client.list_networks(
            **neutron_opts)['networks'])
        resource_usage['subnet'] = len(neutron_client.list_subnets(
            **neutron_opts)['subnets'])
        # Read cinder usages
        resource_usage['volumes'] = len(cinder_client.volumes.list(
            search_opts=cinder_opts))
        resource_usage_all[current_region] = resource_usage
    return resource_usage_all


def get_actual_limits(session, regions, project_id):
    resource_usage = collections.defaultdict(dict)
    for current_region in regions:
        nova_client = nv_client.Client(NOVA_API_VERSION,
                                       session=session,
                                       region_name=current_region)
        neutron_client = nt_client.Client(NEUTRON_API_VERSION,
                                          session=session,
                                          region_name=current_region)
        cinder_client = ci_client.Client(CINDER_API_VERSION,
                                         session=session,
                                         region_name=current_region)
        updated_nova_quota = nova_client.quotas.get(project_id)
        updated_neutron_quota = neutron_client.show_quota(
            project_id)['quota']['network']
        updated_cinder_quota = cinder_client.quotas.get(project_id)
        resource_usage.update({current_region: [updated_nova_quota.instances,
                              updated_neutron_quota,
                              updated_cinder_quota.volumes]})
    return resource_usage


def create_resources(openstack_drivers):
    nova_client = openstack_drivers[1]
    neutron_client = openstack_drivers[2]
    cinder_client = openstack_drivers[3]
    volume = cinder_client.volumes.create(VOLUME_SIZE,
                                          name=VOLUME_NAME)
    flavor = nova_client.flavors.create(
        FLAVOR_NAME, 128, 1, 1, flavorid='auto')
    network_body = {'network': {'name': NETWORK_NAME, 'admin_state_up': True}}
    network = neutron_client.create_network(body=network_body)
    body_create_subnet = {
        "subnets": [
            {
                'cidr': SUBNET_RANGE,
                'ip_version': 4,
                'network_id': network['network']['id'],
                'name': SUBNET_NAME
            }
        ]
    }
    subnet = neutron_client.create_subnet(body=body_create_subnet)
    return {
        'subnet_id': subnet['subnets'][0]['id'],
        'network_id': network['network']['id'],
        'flavor_id': flavor.id,
        'volume_ids': [volume.id]
    }


def set_default_quota(session, regions, project_id, **quota_to_set):
    for current_region in regions:
        nova_client = nv_client.Client(NOVA_API_VERSION,
                                       session=session,
                                       region_name=current_region)
        nova_client.quotas.update(project_id, **quota_to_set)


def update_quota_for_class(token, class_name, new_quota_values):
    body = json.dumps(new_quota_values)
    headers, url_string = get_urlstring_and_headers(token, quota_class_api_url)
    url_string = url_string + class_name
    response = requests.put(url_string, headers=headers, data=body)
    return response.text


def get_quota_for_class(token, class_name):
    headers, url_string = get_urlstring_and_headers(token, quota_class_api_url)
    url_string = url_string + class_name
    response = requests.get(url_string, headers=headers)
    return response.text


def delete_quota_for_class(token, class_name):
    headers, url_string = get_urlstring_and_headers(token, quota_class_api_url)
    url_string = url_string + class_name
    response = requests.delete(url_string, headers=headers)
    return response.text
