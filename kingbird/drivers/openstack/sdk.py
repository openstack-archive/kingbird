# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''
OpenStack Driver
'''

import argparse

from openstackclient.common import clientmanager
from os_client_config import config as cloud_config
from oslo_log import log

from kingbird.common import context
from kingbird.drivers.openstack.cinder_v2 import CinderClient
from kingbird.drivers.openstack.keystone_v3 import KeystoneClient
from kingbird.drivers.openstack.neutron_v2 import NeutronClient
from kingbird.drivers.openstack.nova_v2 import NovaClient

LOG = log.getLogger(__name__)


class OpenStackDriver(object):
    def __init__(self, ctx, region_name=None, token=None):
        self.os_client = self._create_connection(ctx, region_name, token)
        self.nova_client = NovaClient(self.os_client.compute)
        self.cinder_client = CinderClient(self.os_client.volume)
        self.neutron_client = NeutronClient(self.os_client.network)
        self.keystone_client = KeystoneClient(self.os_client.identity)

    def _create_connection(self, ctx, region_name=None, token=None):
        # Create cloudmanager object to connect to openstack
        if isinstance(ctx, dict):
            ctx = context.RequestContext.from_dict(ctx)
        kwargs = {
            'auth_url': ctx.auth_url,
            'default_domain': ctx.domain,
            'tenant_name': ctx.tenant_name,
            'username': ctx.user_name,
            'password': ctx.password,
            'token': token,
            'region_name': region_name or ctx.region_name,
            'cloud': ''
        }
        parser = argparse.ArgumentParser()
        clientmanager.build_plugin_option_parser(parser).parse_args()
        options = argparse.Namespace(**kwargs)
        api_version = {}
        # auth_type below defines the type of authentication to be used
        cc = cloud_config.OpenStackConfig(
            override_defaults={
                'interface': None,
                'auth_type': 'token' if token else 'password',
                },
            )

        cloud = cc.get_one_cloud(
            cloud=options.cloud,
            argparse=options,
            )

        for mod in clientmanager.PLUGIN_MODULES:
            default_version = getattr(mod, 'DEFAULT_API_VERSION', None)
            option = mod.API_VERSION_OPTION.replace('os_', '')
            version_opt = str(cloud.config.get(option, default_version))
            if version_opt:
                api = mod.API_NAME
                api_version[api] = version_opt
        verify = True
        os_client = clientmanager.ClientManager(cli_options=cloud,
                                                verify=verify,
                                                api_version=api_version)
        os_client.auth_ref
        return os_client

    def get_all_regions(self):
        return self.keystone_client.get_regions()

    def get_enabled_projects(self):
        return self.keystone_client.get_enabled_projects()

    def get_resource_usages(self, project_id):
        nova_usages = self.nova_client.get_resource_usages(project_id)
        neutron_usages = self.neutron_client.get_resource_usages(project_id)
        cinder_usages = self.cinder_client.get_resource_usages(project_id)
        return nova_usages, neutron_usages, cinder_usages

    def write_quota_limits(self, project_id, limits_to_write):
        self.nova_client.update_quota_limits(project_id,
                                             limits_to_write['nova'])
        self.cinder_client.update_quota_limits(project_id,
                                               limits_to_write['cinder'])
        self.neutron_client.update_quota_limits(project_id,
                                                limits_to_write['neutron'])

    def delete_quota_limit(self, project_id):
        self.nova_client.delete_quota_limits(project_id)
        self.neutron_client.delete_quota_limits(project_id)
        self.cinder_client.delete_quota_limits(project_id)
