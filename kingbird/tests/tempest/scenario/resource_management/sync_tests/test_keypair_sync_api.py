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


class KingbirdKeyPairSyncTest(base.BaseKBKeypairTest,
                              base.BaseKingbirdClass):

    @decorators.idempotent_id('5024d38b-a46a-4ebb-84be-40c9929eb864')
    def test_kingbird_keypair_sync(self):
        # Keypairs created should be available in the response list
        # Create 2 keypairs:
        job_details = self._keypair_sync_job_create(FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Check for resources in target_regions
        self._check_keypairs_in_target_region(job_details['target'],
                                              job_details['keys'])
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('8eeb04d1-6371-4834-b2e1-0d2dbed98cd5')
    def test_get_kingbird_sync_list(self):
        job_details = self._keypair_sync_job_create(FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_list()
        self.assertEqual(job_list_resp['job_set'][0]['id'],
                         job_details['job_id'])
        # Clean_up the database entries and resources
        self.delete_db_entries(job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('fed7e0b3-0d47-4729-9959-8b6b14230f48')
    def test_get_sync_job_details(self):
        job_details = self._keypair_sync_job_create(FORCE)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        job_list_resp = self.get_sync_job_detail(job_details['job_id'])
        key_list = job_details['keys']
        for i in range(len(key_list)):
            for j in range(len(job_list_resp.get('job_set'))):
                if key_list[i] in job_list_resp.get('job_set')[j].values():
                    self.assertEqual(
                        job_list_resp.get('job_set')[j].get('resource'),
                        key_list[i])
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('resource_type'),
            consts.KEYPAIR_RESOURCE_TYPE)
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('f5701f6a-183b-41fe-b0ab-e0ddef3fbd86')
    def test_get_active_jobs(self):
        job_details = self._keypair_sync_job_create(FORCE)
        active_job = self.get_sync_job_list(consts.JOB_ACTIVE)
        status = active_job.get('job_set')[0].get('sync_status')
        self.assertEqual(status, consts.JOB_PROGRESS)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('9e3fd15b-e170-4fa6-877c-ad4c22a137af')
    def test_delete_active_jobs(self):
        job_details = self._keypair_sync_job_create(FORCE)
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
        # Clean_up the database entries
        self.delete_db_entries(job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('adf565b1-c076-4273-b7d2-305cc144d0e2')
    def test_delete_already_deleted_job(self):
        job_details = self._keypair_sync_job_create(FORCE)
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " %
                                   job_details['job_id']))
        self.delete_db_entries(job_details['job_id'])
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "404 *",
                                self.delete_db_entries, job_details['job_id'])
        self._cleanup_resources(job_details['keys'], job_details['target'],
                                self.client.user_id)

    @decorators.idempotent_id('fcdf50e0-1f7f-4844-8806-23de0fb221d6')
    def test_keypair_sync_with_force_true(self):
        job_details_1 = self._keypair_sync_job_create(FORCE)
        job_id_1 = job_details_1['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        job_details_2 = self._keypair_sync_job_create(FORCE)
        job_id_2 = job_details_2['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_2))
        # Clean_up the database entries
        self.delete_db_entries(job_id_2)
        self._cleanup_resources(job_details_2['keys'], job_details_2['target'],
                                self.client.user_id)

    @decorators.idempotent_id('a340a910-d367-401e-b79a-0a979a3ce65b')
    def test_keypair_sync_with_force_false(self):
        job_details_1 = self._keypair_sync_job_create(DEFAULT_FORCE)
        job_id_1 = job_details_1['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        job_details_2 = self._keypair_sync_job_create(DEFAULT_FORCE,
                                                      job_details_1['keys'])
        job_id_2 = job_details_2['job_id']
        utils.wait_until_true(
            lambda: self._check_job_status(),
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
        self._cleanup_resources(job_details_2['keys'], job_details_2['target'],
                                self.client.user_id)
