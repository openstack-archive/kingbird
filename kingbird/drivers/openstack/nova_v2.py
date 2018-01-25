# Copyright 2016 Ericsson AB

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
import collections

from oslo_log import log

from kingbird.common import consts
from kingbird.common import exceptions
from kingbird.drivers import base

from novaclient import client

LOG = log.getLogger(__name__)
API_VERSION = '2.37'


class NovaClient(base.DriverBase):
    """Nova V2.37 driver."""

    def __init__(self, region, session, disabled_quotas=None):
        try:
            self.nova_client = client.Client(API_VERSION,
                                             session=session,
                                             region_name=region)
            if disabled_quotas:
                self.enabled_quotas = list(set(consts.NOVA_QUOTA_FIELDS) -
                                           set(disabled_quotas))
                self.no_neutron = True if 'floatingips' in self.enabled_quotas \
                    or 'fixedips' in self.enabled_quotas else False
        except exceptions.ServiceUnavailable:
            raise

    def get_resource_usages(self, project_id):
        """Collect resource usages for a given project.

        :params: project_id
        :return: dictionary of corresponding resources with its usage
        """
        try:
            # The API call does not give usage for keypair, fixed ips &
            # metadata items. Have raised a bug for that.
            limits = self.nova_client.limits.get(
                tenant_id=project_id).to_dict()
            resource_usage = collections.defaultdict(dict)
            resource_usage['ram'] = limits['absolute']['totalRAMUsed']
            resource_usage['cores'] = limits['absolute']['totalCoresUsed']
            resource_usage['instances'] = \
                limits['absolute']['totalInstancesUsed']
            # If neutron is not enabled, calculate below resources from nova
            if self.no_neutron:
                resource_usage['security_groups'] = \
                    limits['absolute']['totalSecurityGroupsUsed']
                resource_usage['floating_ips'] = \
                    limits['absolute']['totalFloatingIpsUsed']
            # For time being, keypair is calculated in below manner.
            resource_usage['key_pairs'] = \
                len(self.nova_client.keypairs.list())
            return resource_usage
        except exceptions.InternalError:
            raise

    def update_quota_limits(self, project_id, **new_quota):
        """Update quota limits for a given project.

        :params: project_id, dictionary with the quota limits to update
        :return: Nothing
        """
        try:
            if not self.no_neutron:
                if 'floating_ips' in new_quota:
                    del new_quota['floating_ips']
                if 'fixed_ips' in new_quota:
                    del new_quota['fixed_ips']
                if 'security_groups' in new_quota:
                    del new_quota['security_groups']
            return self.nova_client.quotas.update(project_id,
                                                  **new_quota)
        except exceptions.InternalError:
            raise

    def delete_quota_limits(self, project_id):
        """Delete/Reset quota limits for a given project.

        :params: project_id
        :return: Nothing
        """
        try:
            return self.nova_client.quotas.delete(project_id)
        except exceptions.InternalError:
            raise

    def get_keypairs(self, res_id):
        """Display keypair of the specified User.

        :params: resource_identifier
        :return: Keypair
        """
        try:
            keypair = self.nova_client.keypairs.get(res_id)
            LOG.info("Source Keypair: %s", keypair.name)
            return keypair

        except Exception as exception:
            LOG.error('Exception Occurred: %s', exception.message)
            pass

    def create_keypairs(self, force, keypair):
        """Create keypair for the specified User.

        :params: keypair, force
        :return: Creates a Keypair
        """
        if force:
            try:
                self.nova_client.keypairs.delete(keypair)
                LOG.info("Deleted Keypair: %s", keypair.name)
            except Exception as exception:
                LOG.error('Exception Occurred: %s', exception.message)
                pass
            LOG.info("Created Keypair: %s", keypair.name)
        return self.nova_client.keypairs. \
            create(keypair.name,
                   public_key=keypair.public_key)

    def get_flavor(self, res_id):
        """Get Flavor for a specified context."""
        try:
            res_id = self.nova_client.flavors.find(name=res_id)
            flavor = self.nova_client.flavors.get(res_id)
            LOG.info("Source Flavor: %s", flavor.name)
            return flavor
        except exceptions.ResourceNotFound():
            LOG.error('Exception Occurred: Source Flavor %s not available',
                      res_id)

    def get_flavor_access_tenant(self, res_id):
        """Get tenant which has access to the Flavor."""
        try:
            access_tenants = [access.tenant_id for access in
                              self.nova_client.
                              flavor_access.list(flavor=res_id)]
            LOG.info("Access to only : %s", access_tenants)
            return access_tenants
        except exceptions.InternalError():
            LOG.error('Exception Occurred couldnot find access tenants.')
            pass

    def check_and_delete_flavor_in_target_region(self, flavor,
                                                 resource_flavor):
        """Check for the flavor and then delete it."""
        try:
            target_flavor = self.get_flavor(flavor.name)
            if target_flavor:
                resource_flavor.pop("flavorid", None)
                flavor_list = self.nova_client.flavors.list(is_public=None)
                for target_region_flavor in flavor_list:
                    if target_region_flavor.name == flavor.name:
                        self.nova_client.flavors.delete(
                            target_region_flavor.id)
                        LOG.info("Deleted Flavor: %s", flavor.name)
                        break
        except Exception:
            LOG.error('Exception Occurred: %s not available', flavor.id)
            pass

    def create_flavor(self, force, flavor, access_tenants=None):
        """Create Flavor in target regions."""
        resource_flavor = flavor._info.copy()
        resource_flavor.update({'flavorid': resource_flavor['id']})
        resource_flavor.pop("links", None)
        resource_flavor.pop("OS-FLV-DISABLED:disabled", None)
        resource_flavor["ephemeral"] = resource_flavor[
            "OS-FLV-EXT-DATA:ephemeral"]
        resource_flavor.pop("OS-FLV-EXT-DATA:ephemeral", None)
        resource_flavor.pop("os-flavor-access:is_public", None)
        resource_flavor.pop("id", None)
        if not resource_flavor['swap']:
            resource_flavor.pop("swap", None)
        if not flavor.is_public:
            resource_flavor.update({'is_public': False})
        if force:
            self.check_and_delete_flavor_in_target_region(
                flavor, resource_flavor)
        target_flavor = self.nova_client.flavors.create(**resource_flavor)
        target_flavor_properties = flavor.get_keys()
        if target_flavor_properties:
            try:
                target_flavor.set_keys(target_flavor_properties)
            except Exception as e:
                LOG.error(_("Failed to set flavor property: %s"), e)
        if access_tenants:
            for tenant in access_tenants:
                self.nova_client.flavor_access.add_tenant_access(
                    target_flavor.id, tenant)
                LOG.info('%(flavor)s Access Granted to %(tenant)s'
                         % {'flavor': target_flavor.name, 'tenant': tenant})
        return target_flavor
