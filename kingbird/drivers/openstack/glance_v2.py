# Copyright 2017 Ericsson AB.

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
from oslo_log import log

from kingbird.common import exceptions
from kingbird.drivers.openstack.keystone_v3 import KeystoneClient

from glanceclient import Client

LOG = log.getLogger(__name__)
API_VERSION = '2'


class GlanceClient(object):
    """Glance V2 driver."""

    def __init__(self, region, context):
        """Create Glance Object.

        :param region: Region to which glance object
            has to be created.

        :param context: context object.

        """
        try:
            LOG.info('Creating Glance Object')
            self.keystone_client = KeystoneClient()
            service_id = [service.id for service in
                          self.keystone_client.services_list
                          if service.type == 'image'][0]

            glance_endpoint = [endpoint.url for endpoint in
                               self.keystone_client.endpoints_list
                               if endpoint.service_id == service_id
                               and endpoint.region == region and
                               endpoint.interface == 'public'][0]
            params = dict()
            params['identity_headers'] = self.generate_identity_headers(
                context)
            self.glance_client = Client(str(API_VERSION), glance_endpoint,
                                        **params)
        except exceptions.ServiceUnavailable:
            raise

    def generate_identity_headers(self, context, status='Confirmed'):
        """Extract headers from context object to create glance client.

        :param context: context object.

        """
        return {
            'X-Auth-Token': getattr(context, 'auth_token', None),
            'X-User-Id': getattr(context, 'user', None),
            'X-Tenant-Id': getattr(context, 'project', None),
            'X-Roles': getattr(context, 'roles', []),
            'X-Identity-Status': status,
        }

    def check_image(self, resource_identifier):
        """Get the image details for the specified resource_identifier.

        :param resource_identifier: resource_id for which the details
            have to be retrieved.

        """
        try:
            image = self.glance_client.images.get(resource_identifier)
            LOG.info("Source image: %s", image.name)
            return image.id
        except exceptions.ResourceNotFound():
            LOG.error('Exception Occurred: Source Image %s not available.',
                      resource_identifier)
            pass
