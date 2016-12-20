# Copyright 2017 Ericsson AB
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

from kingbird.tests.tempest.scenario.resource_management \
    import sync_client
from kingbird.tests.tempest.scenario.resource_management. \
    sync_tests import base
from kingbird.tests.tempest.scenario import consts

from novaclient import client as nv_client

FORCE = "True"
DEFAULT_FORCE = "False"


class KingbirdRMTestJSON(base.BaseKingbirdTest):

    @classmethod
    def setup_clients(self):
        super(KingbirdRMTestJSON, self).setup_clients()

    def tearDown(self):
        super(KingbirdRMTestJSON, self).tearDown()

    @classmethod
    def resource_cleanup(self):
        super(KingbirdRMTestJSON, self).resource_cleanup()
        self.delete_resources()

    @classmethod
    def resource_setup(self):
        super(KingbirdRMTestJSON, self).resource_setup()
        self.create_resources()

    @classmethod
    def setup_credentials(self):
        super(KingbirdRMTestJSON, self).setup_credentials()
        self.session = sync_client.get_session()
        self.key_client = sync_client.get_keystone_client(self.session)
        self.regions = sync_client.get_regions(self.key_client)

    def sync_job_create(self, force):
        body = {"resource_set": {"resource_type": consts.RESOURCE_TYPE,
                                 "resources": self.resource_ids["keypairs"],
                                 "source": self.regions[0], "force": force,
                                 "target": self.regions[1:]}}
        response = self.sync_keypair(self.resource_ids["project_id"], body)
        return response

    def delete_entries_in_db(self, project, job):
        response = self.delete_db_entries(self.resource_ids["project_id"], job)
        return response

    def test_keypair_sync(self):
        response = self.sync_job_create(force=FORCE)
        self.wait_for_keypair_sync_to_complete()
        job_id = response.json().get('job_status').get('id')
        self.assertEqual(response.status_code, 200)
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
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_get_sync_list(self):
        response = self.sync_job_create(force=FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        job_list_resp = self.get_sync_list(self.resource_ids["project_id"])
        self.assertEqual(job_list_resp.status_code, 200)
        # Clean_up the database entries
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_get_sync_job_details(self):
        response = self.sync_job_create(force=FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        job_list_resp = self.get_sync_list(self.resource_ids["project_id"],
                                           job_id)
        self.assertEqual(job_list_resp.status_code, 200)
        self.assertEqual(
            job_list_resp.json().get('job_set')[0].get('resource'),
            self.resource_ids["keypairs"][0])
        self.assertEqual(
            job_list_resp.json().get('job_set')[1].get('resource'),
            self.resource_ids["keypairs"][1])
        self.assertEqual(
            job_list_resp.json().get('job_set')[0].get('resource_type'),
            consts.RESOURCE_TYPE)
        # Clean_up the database entries
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_get_active_jobs(self):
        response = self.sync_job_create(force=FORCE)
        job_id = response.json().get('job_status').get('id')
        action = consts.ACTIVE_JOBS
        active_job = self.get_sync_list(self.resource_ids["project_id"],
                                        action)
        status = active_job.json().get('job_set')[0].get('sync_status')
        self.assertEqual(active_job.status_code, 200)
        self.assertEqual(status, consts.JOB_PROGRESS)
        self.wait_for_keypair_sync_to_complete()
        # Clean_up the database entries
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_delete_active_jobs(self):
        response = self.sync_job_create(force=FORCE)
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        # Actual result when we try and delete an active_job
        self.assertEqual(response, 406)
        # Clean_up the database entries
        self.wait_for_keypair_sync_to_complete()
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_delete_already_deleted_job(self):
        response = self.sync_job_create(force=FORCE)
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        # Actual result when we try and delete an active_job
        self.assertEqual(response, 406)
        # Clean_up the database entries
        self.wait_for_keypair_sync_to_complete()
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 404)

    def test_keypair_sync_with_force_true(self):
        response = self.sync_job_create(force=FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)
        response = self.sync_job_create(force=FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response.status_code, 200)
        job_id = response.json().get('job_status').get('id')
        # Clean_up the database entries
        response = self.delete_entries_in_db(self.resource_ids["project_id"],
                                             job_id)
        self.assertEqual(response, 200)

    def test_keypair_sync_with_force_false(self):
        response_1 = self.sync_job_create(force=DEFAULT_FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response_1.status_code, 200)
        job_id_1 = response_1.json().get('job_status').get('id')
        response_2 = self.sync_job_create(force=DEFAULT_FORCE)
        self.wait_for_keypair_sync_to_complete()
        self.assertEqual(response_2.status_code, 200)
        job_id_2 = response_2.json().get('job_status').get('id')
        job_list_resp = self.get_sync_list(self.resource_ids["project_id"],
                                           job_id_2)
        self.assertEqual(job_list_resp.status_code, 200)
        # This job fail because resoruce is already created.
        # We can use force to recreate that resource.
        self.assertEqual(
            job_list_resp.json().get('job_set')[0].get('sync_status'),
            consts.JOB_FAILURE)
        self.assertEqual(
            job_list_resp.json().get('job_set')[1].get('sync_status'),
            consts.JOB_FAILURE)
        # Clean_up the database entries
        delete_response_1 = self.delete_entries_in_db(
            self.resource_ids["project_id"], job_id_1)
        delete_response_2 = self.delete_entries_in_db(
            self.resource_ids["project_id"], job_id_2)
        self.assertEqual(delete_response_1, 200)
        self.assertEqual(delete_response_2, 200)
