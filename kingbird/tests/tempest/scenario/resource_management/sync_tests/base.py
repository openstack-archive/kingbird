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

import time

from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
import tempest.test

from kingbird.tests.tempest.scenario.resource_management \
    import sync_client

CONF = config.CONF
# Time to wait for sync to finish
TIME_FOR_KEYPAIR_SYNC = CONF.kingbird.TIME_FOR_KEYPAIR_SYNC


class BaseKingbirdTest(api_version_utils.BaseMicroversionTest,
                       tempest.test.BaseTestCase):
    """Base test case class for all Kingbird API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseKingbirdTest, cls).skip_checks()

    def setUp(self):
        super(BaseKingbirdTest, self).setUp()

    @classmethod
    def setup_credentials(cls):
        super(BaseKingbirdTest, cls).setup_credentials()
        session = sync_client.get_session()
        cls.keystone_client = sync_client.get_keystone_client(session)
        cls.regions = sync_client.get_regions(cls.keystone_client)

    @classmethod
    def setup_clients(cls):
        super(BaseKingbirdTest, cls).setup_clients()

    @classmethod
    def create_resources(cls):
        # Create Project, User, flavor, subnet & network for test
        project_name = data_utils.rand_name('kb-project')
        user_name = data_utils.rand_name('kb-user')
        password = data_utils.rand_name('kb-password')
        cls.openstack_details = sync_client.get_openstack_drivers(
            cls.keystone_client,
            cls.regions[0],
            project_name,
            user_name,
            password)
        cls.openstack_drivers = cls.openstack_details['os_drivers']
        cls.token = cls.openstack_details['token']
        cls.resource_ids = sync_client.create_resources(cls.openstack_drivers)
        cls.resource_ids.update(cls.openstack_details)
        cls.session = cls.openstack_details['session']

    @classmethod
    def resource_cleanup(cls):
        super(BaseKingbirdTest, cls).resource_cleanup()

    @classmethod
    def wait_for_keypair_sync_to_complete(cls):
        time.sleep(TIME_FOR_KEYPAIR_SYNC)

    @classmethod
    def delete_resources(cls):
        sync_client.resource_cleanup(cls.openstack_drivers, cls.regions,
                                     cls.resource_ids, cls.session)

    @classmethod
    def sync_keypair(cls, project_id, post_body):
        response = sync_client.sync_keypair(cls.token, project_id, post_body)
        return response

    @classmethod
    def get_sync_list(cls, project_id, action=None):
        response = sync_client.get_sync_list(cls.token, project_id, action)
        return response

    @classmethod
    def delete_db_entries(cls, project_id, job_id):
        response = sync_client.delete_db_entries(cls.token, project_id,
                                                 job_id)
        return response
