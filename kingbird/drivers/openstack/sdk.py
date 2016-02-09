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

from kingbird.common import consts
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
               help='keystone authorization url'),
    cfg.StrOpt('identity_url',
               help='keystone service url'),
    cfg.StrOpt('admin_username',
               default='admin',
               help='username of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_password',
               default='admin',
               help='password of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant',
               default='admin',
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
        self.services_list = []
        admin_kwargs = {
            'user_name': cfg.CONF.admin_creds.admin_username,
            'password': cfg.CONF.admin_creds.admin_password,
            'tenant_name': cfg.CONF.admin_creds.admin_tenant,
            'auth_url': cfg.CONF.admin_creds.auth_url,
            'tenant_id': cfg.CONF.admin_creds.admin_tenant_id,
            'project_domain':
                cfg.CONF.admin_creds.admin_tenant_domain_name,
            'user_domain': cfg.CONF.admin_creds.admin_user_domain_name
            }
        if 'keystone' in OpenStackDriver.os_clients_dict:
            self.keystone_client = OpenStackDriver.os_clients_dict['keystone']
        else:
            self.keystone_client = KeystoneClient(**admin_kwargs)
            OpenStackDriver.os_clients_dict['keystone'] = self.keystone_client
        self.services_list = self.keystone_client.keystone_client.\
            services.list()
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
            self.cinder_client = CinderClient(region_name,
                                              self.keystone_client.session)
            self.neutron_client = NeutronClient(region_name,
                                                self.keystone_client.session)
            OpenStackDriver.os_clients_dict[region_name][
                'extension'] = self.neutron_client.neutron_client.\
                list_extensions()
            self.disabled_quotas = self._get_disabled_quotas(region_name)
            self.nova_client = NovaClient(region_name, self.disabled_quotas,
                                          self.keystone_client.session)
            OpenStackDriver.os_clients_dict[
                region_name] = collections.defaultdict(dict)
            OpenStackDriver.os_clients_dict[region_name][
                'nova'] = self.nova_client
            OpenStackDriver.os_clients_dict[region_name][
                'cinder'] = self.cinder_client
            OpenStackDriver.os_clients_dict[region_name][
                'neutron'] = self.neutron_client

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

    def _get_disabled_quotas(self, region):
        # Cinder
        disabled_quotas = []
        if not self._is_service_enabled('volume'):
            disabled_quotas.extend(consts.CINDER_QUOTA_FIELDS)
        # Neutron
        if not self._is_service_enabled('network'):
            disabled_quotas.extend(consts.NEUTRON_QUOTA_FIELDS)
        else:
            # Remove the nova network quotas
            disabled_quotas.extend(['floating_ips', 'fixed_ips'])
            if self._is_extension_supported('security-group', region):
                # If Neutron security group is supported, disable Nova quotas
                disabled_quotas.extend(['security_groups',
                                        'security_group_rules'])
            else:
                # If Nova security group is used, disable Neutron quotas
                disabled_quotas.extend(['security_group',
                                        'security_group_rule'])
            try:
                if not self._is_extension_supported('quotas', region):
                    disabled_quotas.extend(consts.NEUTRON_QUOTA_FIELDS)
            except Exception:
                LOG.exception("There was an error checking if the Neutron "
                              "quotas extension is enabled.")
        return disabled_quotas

    def _is_service_enabled(self, service):
        for current_service in self.services_list:
            if service in current_service.type:
                return True
        return False

    def _is_extension_supported(self, extension, region):
        for current_extension in OpenStackDriver.os_clients_dict[
            region]['extension']['extensions']:
            if extension in current_extension['alias']:
                return True
        return False
