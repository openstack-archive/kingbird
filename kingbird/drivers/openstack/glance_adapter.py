# Copyright 2017 Ericsson AB.
#
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
from kingbird.drivers.openstack.glance_v2 import GlanceClient

LOG = log.getLogger(__name__)
API_VERSION = '2'


def check_dependent_images(context, region, image_id):
    """Check Dependent Images for a given image.

    :param region: source_region
    :param image_id: ID of the image to get dependent image details.
    """
    source_glance_client = GlanceClient(region, context)
    source_image = source_glance_client.get_image(image_id)
    if source_image.disk_format == 'ami':
        try:
            kernel_image = source_glance_client.\
                get_image(source_image.kernel_id)
            kernel_disk_format = getattr(kernel_image, 'disk_format', None)
            if kernel_disk_format is None or kernel_disk_format != 'aki':
                raise exceptions.DependentImageNotFound()
            LOG.info('Kernel Image Found: %(kernel_image)s in %(region)s'
                     % {'kernel_image': kernel_image.id,
                        'region': region})
            ramdisk_image = source_glance_client.\
                get_image(source_image.ramdisk_id)
            ramdisk_disk_format = getattr(ramdisk_image, 'disk_format', None)
            if ramdisk_disk_format is None or ramdisk_disk_format != 'ari':
                raise exceptions.DependentImageNotFound()
            LOG.info('ram disk Image Found: %(ramdisk_image)s in %(region)s'
                     % {'ramdisk_image': ramdisk_image.id,
                        'region': region})

        except exceptions.DependentImageNotFound():
            raise

        return {
            'kernel_image': kernel_image,
            'ramdisk_image': ramdisk_image
        }

    elif source_image.disk_format in ['qcow2', 'aki', 'ari']:
        return None

    else:
        raise exceptions.ImageFormatNotSupported()
