# Copyright 2017 Ericsson AB.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import kingbirdclient
from tempest import config
from tempest.lib import decorators

from kingbird.tests.tempest.scenario import consts
from kingbird.tests.tempest.scenario.resource_management.sync_tests \
    import base
from kingbird.tests import utils


CONF = config.CONF

FORCE = "True"
DEFAULT_FORCE = "False"


class KingbirdImageSyncTest(base.BaseKBImageTest, base.BaseKingbirdClass):
    """Here we test the basic operations of images."""

    @decorators.idempotent_id('f06e43f5-b4e5-40af-92f5-1d280e398d9b')
    def test_qcow2_force_image_sync(self):
        """Here we test these functionalities.

        Register image, upload the image file, get image and check
        if image is created in target regions.
        """
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private'
        }
        job_details = self._image_sync_job_create(FORCE, **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], FORCE, **create_params)
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('791c9c00-d409-4cae-a4b0-306f4dc15abb')
    def test_qcow2_force_image_sync_with_extra_specs(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
            "architecture": 'arm',
            "hypervisor_type": 'qemu'
        }
        job_details = self._image_sync_job_create(FORCE, **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], FORCE, **create_params)
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('d93d8da5-05dc-4e34-b1af-910d65aad92b')
    def test_qcow2_image_sync_without_force(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
            "architecture": 'arm',
            "hypervisor_type": 'qemu'
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('9f51e13d-6958-46f3-a193-3352c5f157dc')
    def test_get_kingbird_image_sync_list(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        job_list_resp = self.get_sync_job_list()
        self.assertEqual(job_list_resp['job_set'][0]['id'],
                         job_details['job_id'])
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)
        # Clean_up the database entries and resources.
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('dfc13300-9d88-4266-bff7-3ea3e56521a7')
    def test_get_image_sync_job_details(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_detail(job_details['job_id'])
        for image_id in job_details['images']:
            for j in range(len(job_list_resp.get('job_set'))):
                if image_id in job_list_resp.get('job_set')[j].values():
                    self.assertEqual(
                        job_list_resp.get('job_set')[j].get('resource'),
                        image_id)
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('resource_type'),
            consts.IMAGE_RESOURCE_TYPE)
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)
        # Clean_up the database entries and resources.
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('65bcfd9e-b9e3-42f1-a77a-3efe50e1b619')
    def test_get_active_jobs_image_sync(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        active_job = self.get_sync_job_list(consts.JOB_ACTIVE)
        status = active_job.get('job_set')[0].get('sync_status')
        self.assertEqual(status, consts.JOB_PROGRESS)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('24de7f1d-afde-41eb-8eda-abf92dfee144')
    def test_delete_active_jobs_image_sync(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "406 *",
                                self.delete_db_entries,
                                job_details['job_id'])
        # Actual result when we try and delete an active_job
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])

    @decorators.idempotent_id('8f463390-0773-4e6b-a152-3a077480d4da')
    def test_delete_already_deleted_job(self):
        create_params = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private',
        }
        job_details = self._image_sync_job_create(DEFAULT_FORCE,
                                                  **create_params)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "404 *",
                                self.delete_db_entries, job_details['job_id'])
        # Check for resources in target_regions.
        self._check_images_delete_target_region(
            job_details['admin'], job_details['target'],
            job_details['images'], DEFAULT_FORCE, **create_params)

    def test_sync_ami_image_with_dependent_images(self):
        ari_create_params = {
            "container_format": CONF.image.container_formats[1],
            "disk_format": CONF.image.disk_formats[1],
            "visibility": 'private',
        }
        ari_image = self.create_and_upload_image(**ari_create_params)
        aki_create_params = {
            "container_format": CONF.image.container_formats[2],
            "disk_format": CONF.image.disk_formats[2],
            "visibility": 'private',
        }
        aki_image = self.create_and_upload_image(**aki_create_params)
        ami_create_params = {
            "container_format": CONF.image.container_formats[0],
            "disk_format": CONF.image.disk_formats[0],
            "visibility": 'private',
            "ramdisk_id": ari_image['id'],
            "kernel_id": aki_image['id']
        }
        ami_image = self.create_and_upload_image(**ami_create_params)
        job_details = self._sync_ami_image(DEFAULT_FORCE, ami_image['id'])
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions.
        self._check_and_delete_dependent_images_target_region(
            job_details['admin'], job_details['target'],
            ami_image, DEFAULT_FORCE, **ami_create_params)
        self.delete_db_entries(job_details['job_id'])
