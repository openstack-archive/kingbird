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


class KingbirdTemplateSyncTest(base.BaseKBKeypairTest,
                               base.BaseKBFlavorsTest,
                               base.BaseKBImageTest,
                               base.BaseKingbirdClass):

    @decorators.idempotent_id('5024d38b-a46a-4ebb-84be-40c9929eb865')
    def test_kingbird_template_sync_with_non_admin(self):
        # Keypairs and images can be created by non-admin
        kwargs = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private'
        }
        keypairs = self._create_keypairs()
        images = self._create_images(**kwargs)
        job_details = self.template_sync_job_create_non_admin(
            keypairs, images, FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions
        self._check_keypairs_in_target_region(job_details['keypair_targets'],
                                              keypairs)
        # Clean_up the database entries and resources
        self._check_images_delete_target_region(
            job_details['admin'], job_details['image_targets'],
            images, FORCE, **kwargs)
        self.delete_db_entries(job_details['job_id'])
        self._keypair_cleanup_resources(
            keypairs, job_details['keypair_targets'],
            self.keypair_client.user_id)

    @decorators.idempotent_id('5024d38b-a46a-4ebb-84be-40c9929eb865')
    def test_kingbird_template_sync_with_admin(self):
        # Flavors should be created by admin
        properties = dict()
        properties["ram"] = self.ram
        properties["vcpus"] = self.vcpus
        properties["disk"] = self.disk
        properties["ephemeral"] = self.ephemeral
        properties["swap"] = self.swap
        properties["rxtx"] = self.rxtx
        admin_session = True
        flavors = self._create_flavor(admin_session)
        job_details = self.template_sync_job_create_admin(flavors[0], FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions
        self._check_flavors_in_target_region(job_details['target'],
                                             flavors[0],
                                             job_details['admin'],
                                             **properties)
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(flavors[0], job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('8eeb04d1-6371-4834-b2e1-0d2dbed98cd5')
    def test_get_kingbird_sync_list(self):
        # Keypairs and images can be created by non-admin
        kwargs = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private'
        }
        keypairs = self._create_keypairs()
        images = self._create_images(**kwargs)
        job_details = self.template_sync_job_create_non_admin(
            keypairs, images, DEFAULT_FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_list()
        self.assertEqual(job_list_resp['job_set'][0]['id'],
                         job_details['job_id'])
        # Clean_up the database entries and resources
        self._check_images_delete_target_region(
            job_details['admin'], job_details['image_targets'],
            images, DEFAULT_FORCE, **kwargs)
        self.delete_db_entries(job_details['job_id'])
        self._keypair_cleanup_resources(
            keypairs, job_details['keypair_targets'],
            self.keypair_client.user_id)

    @decorators.idempotent_id('fed7e0b3-0d47-4729-9959-8b6b14230f48')
    def test_get_sync_job_details(self):
        # Keypairs and images can be created by non-admin
        kwargs = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private'
        }
        keypairs = self._create_keypairs()
        images = self._create_images(**kwargs)
        image_list = images.values()
        job_details = self.template_sync_job_create_non_admin(
            keypairs, images, DEFAULT_FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_detail(job_details['job_id'])
        for i in range(len(job_list_resp.get('job_set'))):
            for j in range(len(keypairs)):
                if keypairs[j] in job_list_resp.get('job_set')[i].values():
                    self.assertEqual(
                        job_list_resp.get('job_set')[i].get('resource_type'),
                        consts.KEYPAIR_RESOURCE_TYPE)
                    self.assertEqual(
                        job_list_resp.get('job_set')[i].get('resource'),
                        keypairs[j])
            for k in range(len(images)):
                if image_list[k] in job_list_resp.get('job_set')[i].values():
                    self.assertEqual(
                        job_list_resp.get('job_set')[i].get('resource_type'),
                        consts.IMAGE_RESOURCE_TYPE)
                    self.assertEqual(
                        job_list_resp.get('job_set')[i].get('resource'),
                        image_list[k])
        # Clean_up the database entries and resources
        self._check_images_delete_target_region(
            job_details['admin'], job_details['image_targets'],
            images, DEFAULT_FORCE, **kwargs)
        self.delete_db_entries(job_details['job_id'])
        self._keypair_cleanup_resources(
            keypairs, job_details['keypair_targets'],
            self.keypair_client.user_id)

    @decorators.idempotent_id('adf565b1-c076-4273-b7d2-305cc144d0e2')
    def test_delete_already_deleted_job(self):
        # Keypairs and images can be created by non-admin
        kwargs = {
            "container_format": CONF.image.container_formats[3],
            "disk_format": CONF.image.disk_formats[6],
            "visibility": 'private'
        }
        keypairs = self._create_keypairs()
        images = self._create_images(**kwargs)
        job_details = self.template_sync_job_create_non_admin(
            keypairs, images, FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "404 *",
                                self.delete_db_entries, job_details['job_id'])
        self._check_images_delete_target_region(
            job_details['admin'], job_details['image_targets'],
            images, FORCE, **kwargs)
        self._keypair_cleanup_resources(
            keypairs, job_details['keypair_targets'],
            self.keypair_client.user_id)
