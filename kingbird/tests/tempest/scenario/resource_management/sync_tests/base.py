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

from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
import tempest.test

from kingbird.tests.tempest.scenario.resource_management \
    import resource_sync_client


class BaseKingbirdTest(api_version_utils.BaseMicroversionTest,
                       tempest.test.BaseTestCase):
    """Base test case class for all Kingbird Resource sync API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseKingbirdTest, cls).skip_checks()

    def setUp(self):
        super(BaseKingbirdTest, self).setUp()

    @classmethod
    def setup_credentials(cls):
        super(BaseKingbirdTest, cls).setup_credentials()
        session = resource_sync_client.get_session()
        cls.keystone_client = resource_sync_client.get_keystone_client(session)
        cls.regions = resource_sync_client.get_regions(cls.keystone_client)

    @classmethod
    def setup_clients(cls):
        super(BaseKingbirdTest, cls).setup_clients()

    @classmethod
    def create_resources(cls):
        # Create Project, User, flavor, subnet & network for test
        project_name = data_utils.rand_name('kb-project')
        user_name = data_utils.rand_name('kb-user')
        password = data_utils.rand_name('kb-password')
        cls.openstack_details = resource_sync_client.get_openstack_drivers(
            cls.keystone_client,
            cls.regions[0],
            project_name,
            user_name,
            password)
        cls.openstack_drivers = cls.openstack_details['os_drivers']
        cls.token = cls.openstack_details['token']
        cls.session = cls.openstack_details['session']

    @classmethod
    def resource_cleanup(cls):
        super(BaseKingbirdTest, cls).resource_cleanup()

    @classmethod
    def create_keypairs(cls):
        cls.resource_ids = resource_sync_client.\
            create_keypairs(cls.openstack_drivers)
        cls.resource_ids.update(cls.openstack_details)

    @classmethod
    def delete_keypairs(cls):
        resource_sync_client.cleanup_keypairs(cls.regions,
                                              cls.resource_ids, cls.session)

    @classmethod
    def delete_resources(cls):
        resource_sync_client.cleanup_resources(cls.openstack_drivers,
                                               cls.resource_ids)

    @classmethod
    def sync_keypair(cls, project_id, post_body):
        response = resource_sync_client.sync_resource(cls.token, project_id,
                                                      post_body)
        return response

    @classmethod
    def get_sync_list(cls, project_id, action=None):
        response = resource_sync_client.get_sync_job_list(
            cls.token, project_id, action)
        return response

    @classmethod
    def delete_db_entries(cls, project_id, job_id):
        response = resource_sync_client.delete_db_entries(
            cls.token, project_id, job_id)
        return response
