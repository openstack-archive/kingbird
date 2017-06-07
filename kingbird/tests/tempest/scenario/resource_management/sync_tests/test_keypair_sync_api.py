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

from kingbird.tests.tempest.scenario.resource_management \
    import resource_sync_client
from kingbird.tests.tempest.scenario.resource_management. \
    sync_tests import base
from kingbird.tests.tempest.scenario import consts
from kingbird.tests import utils

from novaclient import client as nv_client

FORCE = "True"
DEFAULT_FORCE = "False"


class KingbirdKPTest(base.BaseKingbirdTest):

    @classmethod
    def setup_clients(self):
        super(KingbirdKPTest, self).setup_clients()

    def tearDown(self):
        super(KingbirdKPTest, self).tearDown()

    @classmethod
    def resource_cleanup(self):
        super(KingbirdKPTest, self).resource_cleanup()
        self.delete_keypairs()
        self.delete_resources()

    @classmethod
    def resource_setup(self):
        super(KingbirdKPTest, self).resource_setup()
        self.create_resources()
        self.create_keypairs()

    @classmethod
    def setup_credentials(self):
        super(KingbirdKPTest, self).setup_credentials()
        self.session = resource_sync_client.get_session()
        self.key_client = resource_sync_client.\
            get_keystone_client(self.session)
        self.regions = resource_sync_client.get_regions(self.key_client)

    def _check_job_status(self):
        # Wait until the status of the job is not "IN_PROGRESS"
        job_list_resp = self.get_sync_list()
        status = job_list_resp.get('job_set')[0].get('sync_status')
        return status != consts.JOB_PROGRESS

    def _sync_job_create(self, force):
        body = {"resource_type": consts.KEYPAIR_RESOURCE_TYPE,
                "resources": self.resource_ids["keypairs"],
                "source": self.regions[0], "force": force,
                "target": self.regions[1:]}
        response = self.sync_keypair(body)
        return response

    def test_keypair_sync(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        target_regions = self.regions[1:]
        for region in target_regions:
            for keypair in self.resource_ids["keypairs"]:
                nova_client = nv_client.Client(
                    self.resource_ids["nova_version"], session=self.session,
                    region_name=region)
                source_keypair = nova_client.keypairs.get(
                    keypair, self.resource_ids["user_id"])
                self.assertEqual(source_keypair.name, keypair)
        # Clean_up the database entries
        self.delete_db_entries(job_id)

    def test_get_sync_list(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        job_list_resp = self.get_sync_list()
        self.assertEqual(job_list_resp['job_set'][0]['id'], job_id)
        # Clean_up the database entries
        self.delete_db_entries(job_id)

    def test_get_sync_job_details(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        job_list_resp = self.get_sync_detail(job_id)
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('resource'),
            self.resource_ids["keypairs"][0])
        self.assertEqual(
            job_list_resp.get('job_set')[1].get('resource'),
            self.resource_ids["keypairs"][1])
        self.assertEqual(
            job_list_resp.get('job_set')[0].get('resource_type'),
            consts.KEYPAIR_RESOURCE_TYPE)
        # Clean_up the database entries
        self.delete_db_entries(job_id)

    def test_get_active_jobs(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        active_job = self.get_sync_list(consts.JOB_ACTIVE)
        status = active_job.get('job_set')[0].get('sync_status')
        self.assertEqual(status, consts.JOB_PROGRESS)
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        # Clean_up the database entries
        self.delete_db_entries(job_id)

    def test_delete_active_jobs(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "406 *",
                                self.delete_db_entries, job_id)
        # Actual result when we try and delete an active_job
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        self.delete_db_entries(job_id)

    def test_delete_already_deleted_job(self):
        create_response = self._sync_job_create(force=FORCE)
        job_id = create_response.get('job_status').get('id')
        # Clean_up the database entries
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id))
        self.delete_db_entries(job_id)
        self.assertRaisesRegexp(kingbirdclient.exceptions.APIException,
                                "404 *",
                                self.delete_db_entries, job_id)

    def test_keypair_sync_with_force_true(self):
        create_response_1 = self._sync_job_create(force=FORCE)
        job_id_1 = create_response_1.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        create_response_2 = self._sync_job_create(force=FORCE)
        job_id_2 = create_response_2.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_2))
        # Clean_up the database entries
        self.delete_db_entries(job_id_2)

    def test_keypair_sync_with_force_false(self):
        create_response_1 = self._sync_job_create(force=DEFAULT_FORCE)
        job_id_1 = create_response_1.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_1))
        self.delete_db_entries(job_id_1)
        create_response_2 = self._sync_job_create(force=DEFAULT_FORCE)
        job_id_2 = create_response_2.get('job_status').get('id')
        utils.wait_until_true(
            lambda: self._check_job_status(),
            exception=RuntimeError("Timed out waiting for job %s " % job_id_2))
        job_list_resp = self.get_sync_detail(job_id_2)
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
