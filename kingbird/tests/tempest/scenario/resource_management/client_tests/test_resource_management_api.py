# Copyright 2016 Ericsson AB
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

from kingbird.tests.tempest.scenario.resource_management. \
    client_tests import base
from kingbird.tests.tempest.scenario.resource_management \
    import sync_client

from novaclient import client as nv_client

NOVA_API_VERSION = "2.37"
SOURCE_KEYPAIR = "kb_test_keypair"


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
        self.auth_token = self.session.get_token()
        self.key_client = sync_client.get_key_client(self.session)
        self.regions = sync_client.get_regions(self.key_client)

    def test_keypair_sync(self):
        body = {"resource_set": {"resource_type": "keypair",
                                 "resources": SOURCE_KEYPAIR,
                                 "force": "True", "source": self.regions[0],
                                 "target": self.regions[1:]}}
        response = self.sync_keypair(
            self.resource_ids["user_id"],
            body)
        self.wait_sometime_for_sync()
        self.assertEqual(response, 200)
        target_regions = self.regions[1:]
        for region in target_regions:
            nova_client = nv_client.Client(NOVA_API_VERSION,
                                           session=self.session,
                                           region_name=region)
            keypair = nova_client.keypairs.get(SOURCE_KEYPAIR,
                                               self.resource_ids["user_id"])
            self.assertEqual(keypair.name, SOURCE_KEYPAIR)

    def test_keypair_sync_without_source_keypair(self):
        body = {"resource_set": {"resource_type": "keypair",
                                 "resources": "",
                                 "source": self.regions[0],
                                 "target": self.regions[1:]}}
        response = self.sync_keypair(
            self.resource_ids["user_id"],
            body)
        self.assertEqual(response, 404)

    def test_keypair_sync_invalid_resource_type(self):
        body = {"resource_set": {"resource_type": "dummy",
                                 "resources": SOURCE_KEYPAIR,
                                 "source": self.regions[0],
                                 "target": self.regions[1:]}}
        response = self.sync_keypair(
            self.resource_ids["user_id"],
            body)
        self.assertEqual(response, 400)

    def test_keypair_sync_no_source_region(self):
        body = {"resource_set": {"resource_type": "dummy",
                                 "resources": SOURCE_KEYPAIR,
                                 "source": "",
                                 "target": self.regions[1:]}}
        response = self.sync_keypair(
            self.resource_ids["user_id"],
            body)
        self.assertEqual(response, 400)

    def test_keypair_sync_no_target_region(self):
        body = {"resource_set": {"resource_type": "dummy",
                                 "resources": SOURCE_KEYPAIR,
                                 "source": self.regions[0],
                                 "target": [""]}}
        response = self.sync_keypair(
            self.resource_ids["user_id"],
            body)
        self.assertEqual(response, 400)
