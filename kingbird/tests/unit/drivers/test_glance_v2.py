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
from kingbird.drivers.openstack.glance_v2 import GlanceUpload
from kingbird.tests import base
from kingbird.tests import utils

FAKE_ITERATOR = iter([1, 2, 3])
FAKE_ID = utils.UUID4


class FakeService(object):
    """Fake service class used to test service enable testcase."""

    def __init__(self, type_service, name, id):
        self.type = type_service
        self.name = name
        self.id = id


class FakeImage(object):
    """Fake service class used to test service enable testcase."""

    def __init__(self, min_ram, protected, min_disk, name, visibility, tags,
                 owner, architecture, os_version, os_distro, container_format,
                 disk_format, id):
        self.min_ram = min_ram
        self.protected = protected
        self.min_disk = min_disk
        self.name = name
        self.visibility = visibility
        self.tags = tags
        self.owner = owner
        self.architecture = architecture
        self.os_version = os_version
        self.os_distro = os_distro
        self.container_format = container_format
        self.disk_format = disk_format
        self.id = id

    def get(self, attr):
        return getattr(self, attr)

    def iterkeys(self):
        return ",".join(self.__dict__.keys()).split(",")


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

    def common_init(self, mock_glance_client, mock_keystone_client):
        """Keep commonly used variables."""
        fake_service = FakeService('image', 'fake_type', 'fake_id')
        fake_endpoint = FakeEndpoint('fake_url', fake_service.id,
                                     'fake_region', 'public')
        mock_keystone_client().services_list = [fake_service]
        mock_keystone_client().endpoints_list = [fake_endpoint]
        return GlanceClient('fake_region', self.ctx)

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_init(self, mock_glance_client, mock_keystone_client):
        """Test init method of glance."""
        self.common_init(mock_glance_client, mock_keystone_client)
        self.assertEqual(1, mock_glance_client.call_count)

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_get_image(self, mock_glance_client, mock_keystone_client):
        """Test get_image method of glance."""
        Glance_client = self.common_init(mock_glance_client,
                                         mock_keystone_client)
        Glance_client.get_image('fake_resource')
        mock_glance_client().images.get.\
            assert_called_once_with('fake_resource')

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_check_image(self, mock_glance_client, mock_keystone_client):
        """Test get_image method of glance."""
        Glance_client = self.common_init(mock_glance_client,
                                         mock_keystone_client)
        Glance_client.check_image('fake_resource')
        mock_glance_client().images.get.\
            assert_called_once_with('fake_resource')

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_get_image_data(self, mock_glance_client, mock_keystone_client):
        """Test get_image_data method of glance."""
        Glance_client = self.common_init(mock_glance_client,
                                         mock_keystone_client)
        Glance_client.get_image_data('fake_resource')
        mock_glance_client().images.data.\
            assert_called_once_with('fake_resource')

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_image_create_force_false(self, mock_glance_client,
                                      mock_keystone_client):
        """Test create_image method of glance."""
        Glance_client = self.common_init(mock_glance_client,
                                         mock_keystone_client)
        fake_image = FakeImage(0, 'False', 0, 'fake_image', 'public',
                               'fake_tag', 'fake_owner', 'qemu',
                               'fake_version', 'fake_distribution', 'bare',
                               'qcow2', FAKE_ID)
        fake_kwargs = {
            "min_ram": fake_image.min_ram,
            "protected": fake_image.protected,
            "min_disk": fake_image.min_disk,
            "name": fake_image.name,
            "visibility": fake_image.visibility,
            "tags": fake_image.tags,
            "owner": fake_image.owner,
            "architecture": fake_image.architecture,
            "os_version": fake_image.os_version,
            "os_distro": fake_image.os_distro,
            "container_format": fake_image.container_format,
            "disk_format": fake_image.disk_format,
            "id": fake_image.id
            }
        Glance_client.create_image(fake_image, False)
        mock_glance_client().images.create.\
            assert_called_once_with(**fake_kwargs)

    @patch('kingbird.drivers.openstack.glance_v2.KeystoneClient')
    @patch('kingbird.drivers.openstack.glance_v2.Client')
    def test_image_create_force_true(self, mock_glance_client,
                                     mock_keystone_client):
        """Test create_image method of glance."""
        Glance_client = self.common_init(mock_glance_client,
                                         mock_keystone_client)
        fake_image = FakeImage(0, 'False', 0, 'fake_image', 'public',
                               'fake_tag', 'fake_owner', 'qemu',
                               'fake_version', 'fake_distribution', 'bare',
                               'qcow2', FAKE_ID)
        fake_kwargs = {
            "min_ram": fake_image.min_ram,
            "protected": fake_image.protected,
            "min_disk": fake_image.min_disk,
            "name": fake_image.name,
            "visibility": fake_image.visibility,
            "tags": fake_image.tags,
            "owner": fake_image.owner,
            "architecture": fake_image.architecture,
            "os_version": fake_image.os_version,
            "os_distro": fake_image.os_distro,
            "container_format": fake_image.container_format,
            "disk_format": fake_image.disk_format
            }
        Glance_client.create_image(fake_image, True)
        mock_glance_client().images.create.\
            assert_called_once_with(**fake_kwargs)


class TestGlanceUpload(base.KingbirdTestCase):

    def test_init(self):
        """Test init method of GlanceUpload."""
        glance_upload = GlanceUpload(FAKE_ITERATOR)
        self.assertEqual(glance_upload.received, FAKE_ITERATOR)

    def test_read(self):
        """Test read methos of GlanceUpload.

        We send 65536 even though we don't use it.
        Because the read method in GlanceUpload is the replacement
        of read method in glance.
        """
        glance_upload = GlanceUpload(FAKE_ITERATOR).read(65536)
        self.assertEqual(glance_upload, 1)
