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


LOG = log.getLogger(__name__)


class OpenStackDriver(object):

    os_clients_dict = collections.defaultdict(dict)

    def __init__(self, region_name):
        # Check if objects are cached and try to use those
        self.region_name = region_name
        if 'keystone' in OpenStackDriver.os_clients_dict:
            self.keystone_client = OpenStackDriver.os_clients_dict['keystone']
        else:
            self.keystone_client = KeystoneClient()
            OpenStackDriver.os_clients_dict['keystone'] = self.keystone_client
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
        disabled_quotas = []
        # Neutron
        if not self.keystone_client.is_service_enabled('network'):
            disabled_quotas.extend(consts.NEUTRON_QUOTA_FIELDS)
        else:
            # Remove the nova network quotas
            disabled_quotas.extend(['floating_ips', 'fixed_ips'])
            if self.neutron_client.is_extension_supported('security-group'):
                # If Neutron security group is supported, disable Nova quotas
                disabled_quotas.extend(['security_groups',
                                        'security_group_rules'])
            else:
                # If Nova security group is used, disable Neutron quotas
                disabled_quotas.extend(['security_group',
                                        'security_group_rule'])
            try:
                if not self.neutron_client.is_extension_supported('quotas'):
                    disabled_quotas.extend(consts.NEUTRON_QUOTA_FIELDS)
            except Exception:
                LOG.exception("There was an error checking if the Neutron "
                              "quotas extension is enabled.")
        return disabled_quotas
