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
import six

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
        LOG.info("Checking for image in source_region.")
        try:
            image = self.glance_client.images.get(resource_identifier)
            LOG.info("Source image: %s", image.name)
            return image.id
        except exceptions.ResourceNotFound():
            LOG.error('Exception Occurred: Source Image %s not available.',
                      resource_identifier)
            pass

    def get_image(self, resource_identifier):
        """Get the image details for the specified resource_identifier.

        :param resource_identifier: resource_id for which the details
            have to be retrieved.

        """
        LOG.info("Fetching image: %s", resource_identifier)
        return self.glance_client.images.get(resource_identifier)

    def get_image_data(self, resource_identifier):
        """Get the image data of the specified resource.

        :param resource_identifier: resource_id for which the details
            have to be retrieved.

        """
        LOG.info("Fetching data: %s", resource_identifier)
        return self.glance_client.images.data(resource_identifier)

    def create_image(self, image, force, kernel_image=None,
                     ramdisk_image=None):
        """Create image with the same properties of the source image.

        :param kwargs: properties of the image to create in target
            region.
        """
        kwargs = {}
        fields_after_creation = ['status', 'created_at', 'size',
                                 'updated_at', 'file', 'checksum',
                                 'virtual_size', 'schema']

        # split out the usual key and the properties which are top-level
        for key in six.iterkeys(image):
            if key not in fields_after_creation:
                kwargs[key] = image.get(key)

        LOG.warning('Image with id same as that of source_image will be'
                    ' created.If any issue while syncing an image'
                    ' It is because the id already has an entry in'
                    ' target region use --force to avoid this issue.')
        if force:
            LOG.info("Image with a new-id is created.")
            kwargs.pop('id')
        if kernel_image:
            kwargs["kernel-id"] = kernel_image
        if ramdisk_image:
            kwargs["ramdisk-id"] = ramdisk_image
        LOG.info("Creating Image: %s", image.name)
        return self.glance_client.images.create(**kwargs)

    def image_upload(self, image_id, image_data):
        """Upload image to glance.

        :param image_id: UUID of the image to be uploaded.
        """
        LOG.info("Uploading image: %s", image_id)
        return self.glance_client.images.upload(image_id, image_data)


class GlanceUpload(object):
    def __init__(self, data):
        self.received = data

    def read(self, chunk_size):
        """Replace the actual read method in glance.

        Please note that we are using this to replace the actual
        read in glance.
        when we download an image a chunk of 65536 will be written into
        the destination file and
        when we upload an image using a file it reads the entire file
        in the form of chunks(65536 KB). So our approach is to get
        entire imagedata into an iterator and send this 65536kb chunk to
        the glance image upload and there by omitting the usage of file.
        """
        return self.received.next()
