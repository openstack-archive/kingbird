# Copyright (c) 2017 Ericsson AB.
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

from mock import patch

from kingbird.drivers.openstack.glance_v2 import GlanceClient
from kingbird.tests import base
from kingbird.tests import utils


class FakeService(object):
    """Fake service class used to test service enable testcase."""

    def __init__(self, type_service, name, id):
        self.type = type_service
        self.name = name
        self.id = id


class FakeEndpoint(object):
    """Fake Endpoints class used to test service enable testcase."""

    def __init__(self, url, service_id, region, interface):
        self.url = url
        self.service_id = service_id
        self.region = region
        self.interface = interface


class TestGlanceClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestGlanceClient, self).setUp()
        self.ctx = utils.dummy_context()

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_init(self, mock_glance_client, mock_keystone_client):
        """Mock init method of glance."""
        fake_service = FakeService('image', 'fake_type', 'fake_id')
        fake_endpoint = FakeEndpoint('fake_url', fake_service.id,
                                     'fake_region', 'public')
        mock_keystone_client().services_list = [fake_service]
        mock_keystone_client().endpoints_list = [fake_endpoint]
        GlanceClient('fake_region', self.ctx)
        self.assertEqual(1, mock_glance_client.call_count)

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_check_image(self, mock_glance_client, mock_keystone_client):
        """Test get_image method of glance."""
        fake_service = FakeService('image', 'fake_type', 'fake_id')
        fake_endpoint = FakeEndpoint('fake_url', fake_service.id,
                                     'fake_region', 'public')
        mock_keystone_client().services_list = [fake_service]
        mock_keystone_client().endpoints_list = [fake_endpoint]
        glance_client = GlanceClient('fake_region', self.ctx)
        glance_client.check_image('fake_resource')
        mock_glance_client().images.get.\
            assert_called_once_with('fake_resource')
