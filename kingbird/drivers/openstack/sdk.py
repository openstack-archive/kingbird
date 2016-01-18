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
import collections

from oslo_log import log

from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.common.i18n import _LE
from kingbird.common.i18n import _LI

from kingbird.drivers.openstack.cinder_v2 import CinderClient
from kingbird.drivers.openstack.keystone_v3 import KeystoneClient
from kingbird.drivers.openstack.neutron_v2 import NeutronClient
from kingbird.drivers.openstack.nova_v2 import NovaClient

from oslo_config import cfg

LOG = log.getLogger(__name__)

admin_creds_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v3',
               help='keystone authorization url'),
    cfg.StrOpt('identity_url',
               default='http://127.0.0.1:35357/v3',
               help='keystone service url'),
    cfg.StrOpt('admin_username',
               help='username of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_password',
               help='password of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant',
               help='tenant name of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant_id',
               help='tenant name of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_user_domain_name',
               default='Default',
               help='user domain name of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant_domain_name',
               default='Default',
               help='tenant domain name of admin account, needed when'
                    ' auto_refresh_endpoint set to True')
]
admin_creds_opt_group = cfg.OptGroup('admin_creds')
cfg.CONF.register_group(admin_creds_opt_group)
cfg.CONF.register_opts(admin_creds_opts, group=admin_creds_opt_group)


class OpenStackDriver(object):

    os_clients_dict = collections.defaultdict(dict)

    def __init__(self, region_name):
        # Check if objects are cached and try to use those
        self.region_name = region_name
        if region_name in OpenStackDriver.os_clients_dict:
            LOG.info(_LI('Using cached OS client objects'))
            self.nova_client = OpenStackDriver.os_clients_dict[
                region_name]['nova']
            self.cinder_client = OpenStackDriver.os_clients_dict[
                region_name]['cinder']
            self.neutron_client = OpenStackDriver.os_clients_dict[
                region_name]['neutron']
        else:
            # Create new objects and cache them
            LOG.debug(_("Creating fresh OS Clients objects"))
            admin_kwargs = {
                'user_name': cfg.CONF.admin_creds.admin_username,
                'password': cfg.CONF.admin_creds.admin_password,
                'tenant_name': cfg.CONF.admin_creds.admin_tenant,
                'auth_url': cfg.CONF.admin_creds.auth_url,
                'tenant_id': cfg.CONF.admin_creds.admin_tenant_id
                }
            self.nova_client = NovaClient(region_name, **admin_kwargs)
            self.cinder_client = CinderClient(region_name, **admin_kwargs)
            self.neutron_client = NeutronClient(region_name, **admin_kwargs)
            OpenStackDriver.os_clients_dict[
                region_name] = collections.defaultdict(dict)
            OpenStackDriver.os_clients_dict[region_name][
                'nova'] = self.nova_client
            OpenStackDriver.os_clients_dict[region_name][
                'cinder'] = self.cinder_client
            OpenStackDriver.os_clients_dict[region_name][
                'neutron'] = self.neutron_client
        if 'keystone' in OpenStackDriver.os_clients_dict:
            self.keystone_client = OpenStackDriver.os_clients_dict['keystone']
        else:
            self.keystone_client = KeystoneClient(**admin_kwargs)
            OpenStackDriver.os_clients_dict['keystone'] = self.keystone_client

    def get_enabled_projects(self):
        try:
            return self.keystone_client.get_enabled_projects()
        except Exception as exception:
            LOG.error(_LE('Error Occurred: %s'), exception.message)

    def get_resource_usages(self, project_id):
        try:
            nova_usages = self.nova_client.get_resource_usages(project_id)
            neutron_usages = self.neutron_client.get_resource_usages(
                project_id)
            cinder_usages = self.cinder_client.get_resource_usages(project_id)
            return nova_usages, neutron_usages, cinder_usages
        except (exceptions.ConnectionRefused, exceptions.NotAuthorized,
                exceptions.TimeOut):
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]
        except Exception as exception:
            LOG.error(_LE('Error Occurred: %s'), exception.message)

    def write_quota_limits(self, project_id, limits_to_write):
        try:
            self.nova_client.update_quota_limits(project_id,
                                                 limits_to_write['nova'])
            self.cinder_client.update_quota_limits(project_id,
                                                   limits_to_write['cinder'])
            self.neutron_client.update_quota_limits(project_id,
                                                    limits_to_write['neutron'])
        except (exceptions.ConnectionRefused, exceptions.NotAuthorized,
                exceptions.TimeOut):
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]
        except Exception as exception:
            LOG.error(_LE('Error Occurred: %s'), exception.message)

    def delete_quota_limits(self, project_id):
        try:
            self.nova_client.delete_quota_limits(project_id)
            self.neutron_client.delete_quota_limits(project_id)
            self.cinder_client.delete_quota_limits(project_id)
        except (exceptions.ConnectionRefused, exceptions.NotAuthorized,
                exceptions.TimeOut):
            # Delete the cached objects for that region
            del OpenStackDriver.os_clients_dict[self.region_name]
        except Exception as exception:
            LOG.error(_LE('Error Occurred: %s'), exception.message)
