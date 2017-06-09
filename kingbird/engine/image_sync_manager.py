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
                                   source_region, context, resource,
                                   dependent_images=None):
        """Create Region Specific threads."""
        regions_thread = list()
        for region in target_regions:
            thread = threading.Thread(target=self.create_resources,
                                      args=(job_id, region, source_region,
                                            context, resource,
                                            dependent_images))
            regions_thread.append(thread)
            thread.start()
            for region_thread in regions_thread:
                region_thread.join()

    def create_resources(self, job_id, region, source_region, context,
                         resource, dependent_images=None):
        """Create Resources using on threads."""
        source_glance_client = GlanceClient(source_region, context)
        target_glance_client = GlanceClient(region, context)
        if dependent_images:
            try:
                # Kernel image creation and upload.
                kernel_image = dependent_images['kernel_image']
                kernel_image_data = source_glance_client.\
                    get_image_data(kernel_image.id)
                target_kernel_image = target_glance_client.\
                    create_image(kernel_image)
                upload_image = GlanceUpload(kernel_image_data)
                target_glance_client.image_upload(target_kernel_image.id,
                                                  upload_image)
                LOG.info('Kernel_image %(image)s created in %(region)s'
                         % {'image': kernel_image.id, 'region': region})

                # Ramdisk_image creation and upload.
                ramdisk_image = dependent_images['ramdisk_image']
                ramdisk_image_data = source_glance_client.\
                    get_image_data(ramdisk_image.id)
                target_ramdisk_image = target_glance_client.\
                    create_image(ramdisk_image)
                upload_ram_disk_image = GlanceUpload(ramdisk_image_data)
                target_glance_client.\
                    image_upload(target_ramdisk_image.id,
                                 upload_ram_disk_image)
                LOG.info('ramdisk_image %(image)s created in %(region)s'
                         % {'image': ramdisk_image.id, 'region': region})
            except Exception as exc:
                LOG.error('Exception Occurred: %(msg)s in %(region)s'
                          % {'msg': exc.message, 'region': region})

        # Source_image creation and upload.
        try:
            source_image = source_glance_client.get_image(resource)
            source_image_data = source_glance_client.\
                get_image_data(source_image.id)
            target_source_image = target_glance_client.\
                create_image(source_image)
            upload_source_image = GlanceUpload(source_image_data)
            target_glance_client.\
                image_upload(target_source_image.id, upload_source_image)
            LOG.info('source_image %(image)s created in %(region)s'
                     % {'image': source_image.id, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id, region,
                                            source_image.id,
                                            consts.JOB_SUCCESS)
            except exceptions.JobNotFound():
                raise

        except Exception as exc:
            LOG.error('Exception Occurred: %(msg)s in %(region)s'
                      % {'msg': exc.message, 'region': region})
            try:
                db_api.resource_sync_update(context, job_id, region,
                                            source_image.id,
                                            consts.JOB_FAILURE)
            except exceptions.JobNotFound():
                raise
            pass

    def resource_sync(self, context, job_id, payload):
        """Create resources in target regions.

        :param context: request context object.
        :param job_id: ID of the job which triggered image_sync.
        :payload: request payload.
        """
        LOG.info('Triggered image sync.')
        images_thread = list()
        target_regions = payload['target']
        resource_ids = payload.get('resources')
        source_region = payload['source']
        resources = dict()
        for resource in resource_ids:
            resources[resource] = glance_adapter.\
                check_dependent_images(context, source_region, resource)
        for resource in resources:
            dependent_images = resources[resource]
            thread = threading.Thread(target=self.create_resources_in_region,
                                      args=(job_id, target_regions,
                                            source_region, context,
                                            resource, dependent_images))
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
