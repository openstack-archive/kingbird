# Copyright 2017 Ericsson AB.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import mock

from kingbird.engine import flavor_sync_manager
from kingbird.tests import base
from kingbird.tests import utils

DEFAULT_FORCE = False
SOURCE_FLAVOR = 'fake_key1'
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = 'fake_target_region'
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'
FAKE_JOB_ID = utils.UUID1
JOB_RESULT = "SUCCESS"
FAKE_TENANTS = ['fake_tenant_1', 'fake_tenant_2']


class FakeFlavor(object):
    def __init__(self, id, ram, cores, disks, name, swap, rxtx_factor,
                 is_public=True):
        self.id = id
        self.ram = ram
        self.vcpus = cores
        self.disk = disks
        self.name = name
        self.is_public = is_public
        self.swap = swap
        self.rxtx_factor = 1.0


class TestFlavorSyncManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestFlavorSyncManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @mock.patch.object(flavor_sync_manager, 'NovaClient')
    @mock.patch.object(flavor_sync_manager, 'EndpointCache')
    @mock.patch.object(flavor_sync_manager.FlavorSyncManager,
                       'create_resources')
    @mock.patch.object(flavor_sync_manager, 'db_api')
    def test_flavor_sync_force_false_no_access_tenants(
            self, mock_db_api, mock_create_resource, mock_endpoint_cache,
            mock_nova):
        access_tenants = None
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_flavor.return_value = fake_flavor
        mock_db_api().resource_sync_status.return_value = [JOB_RESULT]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_create_resource.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_flavor,
            'fake_session', self.ctxt, access_tenants)
        mock_nova().get_flavor_access_tenant.assert_not_called
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, JOB_RESULT)

    @mock.patch.object(flavor_sync_manager, 'NovaClient')
    @mock.patch.object(flavor_sync_manager, 'EndpointCache')
    @mock.patch.object(flavor_sync_manager.FlavorSyncManager,
                       'create_resources')
    @mock.patch.object(flavor_sync_manager, 'db_api')
    def test_flavor_sync_force_true_no_access_tenants(
            self, mock_db_api, mock_create_resource, mock_endpoint_cache,
            mock_nova):
        access_tenants = None
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_flavor.return_value = fake_flavor
        mock_db_api().resource_sync_status.return_value = [JOB_RESULT]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_create_resource.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_flavor,
            'fake_session', self.ctxt, access_tenants)
        mock_nova().get_flavor_access_tenant.assert_not_called
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, JOB_RESULT)

    @mock.patch.object(flavor_sync_manager, 'NovaClient')
    @mock.patch.object(flavor_sync_manager, 'EndpointCache')
    @mock.patch.object(flavor_sync_manager.FlavorSyncManager,
                       'create_resources')
    @mock.patch.object(flavor_sync_manager, 'db_api')
    def test_flavor_sync_force_false_with_access_tenants(
            self, mock_db_api, mock_create_resource, mock_endpoint_cache,
            mock_nova):
        access_tenants = FAKE_TENANTS
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0, False)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        mock_nova().get_flavor_access_tenant.return_value = access_tenants
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_flavor.return_value = fake_flavor
        mock_db_api().resource_sync_status.return_value = [JOB_RESULT]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_create_resource.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_flavor,
            'fake_session', self.ctxt, access_tenants)
        mock_nova().get_flavor_access_tenant.\
            assert_called_once_with(fake_flavor)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, JOB_RESULT)

    @mock.patch.object(flavor_sync_manager, 'NovaClient')
    @mock.patch.object(flavor_sync_manager, 'EndpointCache')
    @mock.patch.object(flavor_sync_manager.FlavorSyncManager,
                       'create_resources')
    @mock.patch.object(flavor_sync_manager, 'db_api')
    def test_flavor_sync_force_true_with_access_tenants(
            self, mock_db_api, mock_create_resource, mock_endpoint_cache,
            mock_nova):
        access_tenants = FAKE_TENANTS
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0, False)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        mock_nova().get_flavor_access_tenant.return_value = access_tenants
        mock_endpoint_cache().get_session_from_token.\
            return_value = 'fake_session'
        mock_nova().get_flavor.return_value = fake_flavor
        mock_db_api().resource_sync_status.return_value = [JOB_RESULT]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_create_resource.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_flavor,
            'fake_session', self.ctxt, access_tenants)
        mock_nova().get_flavor_access_tenant.\
            assert_called_once_with(fake_flavor)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, JOB_RESULT)

    @mock.patch.object(flavor_sync_manager.FlavorSyncManager,
                       'create_resources')
    def test_create_resources_in_region(self, mock_create_resource):
        access_tenants = None
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0, False)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.create_resources_in_region(FAKE_JOB_ID, payload['force'],
                                       payload['target'], fake_flavor,
                                       'fake_session', self.ctxt,
                                       access_tenants)
        mock_create_resource.assert_called_once_with(
            FAKE_JOB_ID, payload['force'], payload['target'][0], fake_flavor,
            'fake_session', self.ctxt, access_tenants)

    @mock.patch.object(flavor_sync_manager, 'NovaClient')
    @mock.patch.object(flavor_sync_manager, 'db_api')
    def test_create_resources(self, mock_db_api, mock_nova):
        access_tenants = None
        fake_flavor = FakeFlavor('fake_id', 512, 2, 30, 'fake_flavor', 1,
                                 1.0, False)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = True
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_flavor]
        fsm = flavor_sync_manager.FlavorSyncManager()
        fsm.create_resources(FAKE_JOB_ID, payload['force'],
                             payload['target'][0], fake_flavor,
                             'fake_session', self.ctxt, access_tenants)
        mock_nova().create_flavor.assert_called_once_with(
            payload['force'], fake_flavor, access_tenants)
        mock_db_api.resource_sync_update.assert_called_once_with(
            self.ctxt, FAKE_JOB_ID, payload['target'][0], fake_flavor.id,
            JOB_RESULT)
