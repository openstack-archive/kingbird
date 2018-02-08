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

from tempest.lib import decorators

from kingbird.tests.tempest.scenario import consts
from kingbird.tests.tempest.scenario.resource_management.sync_tests \
    import base
from kingbird.tests import utils

FORCE = "True"
DEFAULT_FORCE = "False"


class KingbirdFlavorSyncTest(base.BaseKBFlavorsTest,
                             base.BaseKingbirdClass):

    @decorators.idempotent_id('8261d7b0-be58-43ec-a2e5-300573c3f6c5')
    def test_kingbird_flavor_sync(self):
        # Flavors are created by admin only
        properties = dict()
        properties["ram"] = self.ram
        properties["vcpus"] = self.vcpus
        properties["disk"] = self.disk
        properties["ephemeral"] = self.ephemeral
        properties["swap"] = self.swap
        properties["rxtx"] = self.rxtx
        admin_session = True
        # Flavors created should be available in the response list
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions
        self._check_flavors_in_target_region(job_details['target'],
                                             job_details['flavors'],
                                             job_details['admin'],
                                             **properties)
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('5024d38b-a46a-4ebb-84be-40c9929eb868')
    def test_kingbird_flavor_sync_with_non_admin(self):
        admin_session = False
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "403 *",
                                self._flavor_sync_job_create,
                                FORCE, admin_session)

    @decorators.idempotent_id('8eeb04d1-6371-4834-b2e1-0d2dbed98cd5')
    def test_get_kingbird_sync_list(self):
        # Flavors created should be available in the response list
        admin_session = True
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_list()
        self.assertEqual(job_list_resp['job_set'][0]['id'],
                         job_details['job_id'])
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('fed7e0b3-0d47-4729-9959-8b6b14230f48')
    def test_get_sync_job_details(self):
        admin_session = True
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_detail(job_details['job_id'])
        flavor_list = job_details['flavors']
        for i in range(len(flavor_list)):
            for j in range(len(job_list_resp.get('job_set'))):
                if flavor_list[i] in job_list_resp.get('job_set')[j].values():
                    self.assertEqual(
                        job_list_resp.get('job_set')[j].get('resource'),
                        flavor_list[i])
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('resource_type'),
            consts.FLAVOR_RESOURCE_TYPE)
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('f5701f6a-183b-41fe-b0ab-e0ddef3fbd86')
    def test_get_active_jobs(self):
        admin_session = True
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        active_job = self.get_sync_job_list(consts.JOB_ACTIVE)
        status = active_job.get('job_set')[0].get('sync_status')
        self.assertEqual(status, consts.JOB_PROGRESS)
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('9e3fd15b-e170-4fa6-877c-ad4c22a137af')
    def test_delete_active_jobs(self):
        admin_session = True
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "406 *",
                                self.delete_db_entries,
                                job_details['job_id'])
        # Actual result when we try and delete an active_job
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('adf565b1-c076-4273-b7d2-305cc144d0e2')
    def test_delete_already_deleted_job(self):
        admin_session = True
        job_details = self._flavor_sync_job_create(FORCE, admin_session)
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(job_details['job_id']),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        self.delete_db_entries(job_details['job_id'])
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "404 *",
                                self.delete_db_entries, job_details['job_id'])
        self._flavor_cleanup_resources(job_details['flavors'],
                                       job_details['target'],
                                       job_details['admin'])

    @decorators.idempotent_id('fcdf50e0-1f7f-4844-8806-23de0fb221d6')
    def test_flavor_sync_with_force_true(self):
        admin_session = True
        job_details_1 = self._flavor_sync_job_create(FORCE, admin_session)
        job_id_1 = job_details_1['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(job_id_1),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        job_details_2 = self._flavor_sync_job_create(FORCE, admin_session,
                                                     job_details_1['flavors'])
        job_id_2 = job_details_2['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(job_id_2),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_2))
        # Clean_up the database entries
        self.delete_db_entries(job_id_2)
        self._flavor_cleanup_resources(job_details_2['flavors'],
                                       job_details_2['target'],
                                       job_details_2['admin'])

    @decorators.idempotent_id('a340a910-d367-401e-b79a-0a979a3ce65b')
    def test_flavor_sync_with_force_false(self):
        admin_session = True
        job_details_1 = self._flavor_sync_job_create(DEFAULT_FORCE,
                                                     admin_session)
        job_id_1 = job_details_1['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(job_id_1),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        job_details_2 = self._flavor_sync_job_create(DEFAULT_FORCE,
                                                     admin_session,
                                                     job_details_1['flavors'])
        job_id_2 = job_details_2['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(job_id_2),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_2))
        job_list_resp = self.get_sync_job_detail(job_id_2)
        # This job fail because resoruce is already created.
        # We can use force to recreate that resource.
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('sync_status'),
            consts.JOB_FAILURE)
        self.assertEqual(
            job_list_resp.get('job_set')[1].get('sync_status'),
            consts.JOB_FAILURE)
        # Clean_up the database entries
        self.delete_db_entries(job_id_2)
        self._flavor_cleanup_resources(job_details_2['flavors'],
                                       job_details_2['target'],
                                       job_details_2['admin'])
