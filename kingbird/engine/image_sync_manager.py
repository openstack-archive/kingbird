# Copyright 2017 Ericsson AB.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading

from oslo_log import log as logging

from kingbird.common import consts
from kingbird.common import exceptions
from kingbird.db.sqlalchemy import api as db_api
from kingbird.drivers.openstack import glance_adapter
from kingbird.drivers.openstack.glance_v2 import GlanceClient
from kingbird.drivers.openstack.glance_v2 import GlanceUpload

LOG = logging.getLogger(__name__)


class ImageSyncManager(object):
    """Manages tasks related to resource management."""

    def __init__(self, *args, **kwargs):
        super(ImageSyncManager, self).__init__()

    def create_resources_in_region(self, job_id, target_regions,
                                   source_region, context, resource, force):
        """Create Region Specific threads."""
        regions_thread = list()
        for region in target_regions:
            thread = threading.Thread(target=self.create_resources,
                                      args=(job_id, region, source_region,
                                            context, resource, force))
            regions_thread.append(thread)
            thread.start()
            for region_thread in regions_thread:
                region_thread.join()

    def create_resources(self, job_id, region, source_region, context,
                         resource, force):
        """Check dependent images and create resources in target regions."""
        source_glance_client = GlanceClient(source_region, context)
        target_glance_client = GlanceClient(region, context)
        dependent_images = glance_adapter.check_dependent_images(
            context, source_region, resource)
        if dependent_images is not None:
            result = self.create_dependent_image(
                resource, dependent_images, target_glance_client,
                source_glance_client, region, force)
            self.update_result_in_database(context, job_id, region, resource,
                                           result)
        else:
            result = self.create_independent_image(
                resource, target_glance_client, source_glance_client,
                region, force)
            self.update_result_in_database(context, job_id, region, resource,
                                           result)

    def update_result_in_database(self, context, job_id, region, resource,
                                  result):
        """Update result in database based on the sync operation."""
        job_result = consts.JOB_SUCCESS if result else consts.JOB_FAILURE
        try:
            db_api.resource_sync_update(context, job_id, region,
                                        resource, job_result)
        except exceptions.JobNotFound():
            raise
        pass

    def create_dependent_image(self, resource, dependent_images,
                               target_client, source_client, region, force):
        """Create dependent images along with base image.

        Base image here is Amazon Machine Image(AMI) and
        Dependent images are Amazon Kernel Image(AKI),
        Amazon Ramdisk Image(ARI).

        :param resource: Resource to be synced.
        :param dependent_images: Dependent images for the base image.
        :param target_client: Glance client object for the target_region.
        :param source_client: Glance client object for source_region.
        :param region: Target region in which resource has to be synced.
        :param force: Default force option is False. If '--force'
            is given then force is set to True.
        """
        try:
            kernel_image = dependent_images['kernel_image']
            ramdisk_image = dependent_images['ramdisk_image']
            source_image = source_client.get_image(resource)
            # Create images in target regions.
            target_kernel_image = target_client.\
                create_image(kernel_image, force)
            target_ramdisk_image = target_client.\
                create_image(ramdisk_image, force)
            target_source_image = target_client.\
                create_image(source_image, force, target_kernel_image.id,
                             target_ramdisk_image.id)

            # Fetch and Upload image into glance.
            # Kernel Image upload.
            kernel_image_data = source_client.\
                get_image_data(kernel_image.id)
            upload_kernel_image = GlanceUpload(kernel_image_data)
            target_client.image_upload(target_kernel_image.id,
                                       upload_kernel_image)
            LOG.info('Kernel_image %(image)s uploaded in %(region)s'
                     % {'image': kernel_image.id, 'region': region})

            # Ramdisk image upload.
            ramdisk_image_data = source_client.\
                get_image_data(ramdisk_image.id)
            upload_ram_disk_image = GlanceUpload(ramdisk_image_data)
            target_client.image_upload(target_ramdisk_image.id,
                                       upload_ram_disk_image)
            LOG.info('ramdisk_image %(image)s uploaded in %(region)s'
                     % {'image': ramdisk_image.id, 'region': region})

            # Base 'AMI' image upload.
            source_image_data = source_client.get_image_data(source_image.id)
            upload_source_image = GlanceUpload(source_image_data)
            target_client.image_upload(target_source_image.id,
                                       upload_source_image)
            LOG.info('source_image %(image)s uploaded in %(region)s'
                     % {'image': source_image.id, 'region': region})
            return True
        except Exception as exc:
            LOG.error('Exception Occurred: %(msg)s in %(region)s'
                      % {'msg': exc.message, 'region': region})
            return False

    def create_independent_image(self, resource, target_client,
                                 source_client, region, force):
        """Create independent images.

        Base image here is Qcow2.

        :param resource: Resource to be synced.
        :param target_client: Glance client object for the target_region.
        :param source_client: Glance client object for source_region.
        :param region: Target region in which resource has to be synced.
        :param force: Default force option is False. If '--force'
            is given then force is set to True.
        """
        try:
            source_image = source_client.get_image(resource)
            target_source_image = target_client.create_image(source_image,
                                                             force)
            source_image_data = source_client.get_image_data(source_image.id)
            upload_source_image = GlanceUpload(source_image_data)
            target_client.image_upload(target_source_image.id,
                                       upload_source_image)
            LOG.info('source_image %(image)s uploaded in %(region)s'
                     % {'image': source_image.id, 'region': region})
            return True
        except Exception as exc:
            LOG.error('Exception Occurred: %(msg)s in %(region)s'
                      % {'msg': exc.message, 'region': region})
            return False

    def resource_sync(self, context, job_id, payload):
        """Create resources in target regions.

        Image with same id is created in target_regions and therefore
        if a user wants to syncs the same resource as the ID is already
        used glance throws 409 error in order to avoid that we use --force
        and set force flag to true and there by creates resource without
        fail.

        :param context: request context object.
        :param job_id: ID of the job which triggered image_sync.
        :payload: request payload.
        """
        LOG.info('Triggered image sync.')
        images_thread = list()
        target_regions = payload['target']
        force = eval(str(payload.get('force', False)))
        resource_ids = payload.get('resources')
        source_region = payload['source']
        for resource in resource_ids:
            thread = threading.Thread(target=self.create_resources_in_region,
                                      args=(job_id, target_regions,
                                            source_region, context,
                                            resource, force))
            images_thread.append(thread)
            thread.start()
            for image_thread in images_thread:
                image_thread.join()
        try:
            resource_sync_details = db_api.\
                resource_sync_status(context, job_id)
        except exceptions.JobNotFound:
            raise
        result = consts.JOB_SUCCESS
        if consts.JOB_FAILURE in resource_sync_details:
            result = consts.JOB_FAILURE
        try:
            db_api.sync_job_update(context, job_id, result)
        except exceptions.JobNotFound:
            raise
