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

from mock import patch

from kingbird.common import exceptions
from kingbird.drivers.openstack import glance_adapter
from kingbird.tests import base
from kingbird.tests import utils

FAKE_ID = utils.UUID1
FAKE_KERNEL_ID = utils.UUID2
FAKE_RAMDISK_ID = utils.UUID3


class FakeQCOW2Image(object):
    """Fake QCOW2 image class used to test service enable testcase."""

    def __init__(self, min_ram, protected, min_disk, name, container_format,
                 disk_format, id):
        self.min_ram = min_ram
        self.protected = protected
        self.min_disk = min_disk
        self.name = name
        self.container_format = container_format
        self.disk_format = disk_format
        self.id = id


class FakeAMIimage(object):
    """Fake AMI image class used to test service enable testcase."""

    def __init__(self, min_ram, protected, min_disk, name, container_format,
                 disk_format, kernel_id, ramdisk_id, id):
        self.min_ram = min_ram
        self.protected = protected
        self.min_disk = min_disk
        self.name = name
        self.container_format = container_format
        self.disk_format = disk_format
        self.kernel_id = kernel_id
        self.ramdisk_id = ramdisk_id
        self.id = id


class FakeAKIimage(object):
    """Fake AKI image class used to test service enable testcase."""

    def __init__(self, min_ram, protected, min_disk, name, container_format,
                 disk_format, id):
        self.min_ram = min_ram
        self.protected = protected
        self.min_disk = min_disk
        self.name = name
        self.container_format = container_format
        self.disk_format = disk_format
        self.id = id


class FakeARIimage(object):
    """Fake ARI image class used to test service enable testcase."""

    def __init__(self, min_ram, protected, min_disk, name, container_format,
                 disk_format, id):
        self.min_ram = min_ram
        self.protected = protected
        self.min_disk = min_disk
        self.name = name
        self.container_format = container_format
        self.disk_format = disk_format
        self.id = id


class TestGlanceAdapter(base.KingbirdTestCase):

    def setUp(self):
        super(TestGlanceAdapter, self).setUp()
        self.ctx = utils.dummy_context()

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_check_dependent_images_for_qcow2(self, mock_glance_client):
        fake_image = FakeQCOW2Image(0, 'False', 0, 'fake_image', 'bare',
                                    'qcow2', FAKE_ID)
        mock_glance_client().get_image.return_value = fake_image
        glance_adapter.check_dependent_images('fake_region', self.ctx,
                                              fake_image.id)
        mock_glance_client().get_image.assert_called_once_with(fake_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_check_dependent_images_for_aki(self, mock_glance_client):
        fake_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image', 'aki',
                                  'aki', FAKE_ID)
        mock_glance_client().get_image.return_value = fake_image
        glance_adapter.check_dependent_images('fake_region', self.ctx,
                                              fake_image.id)
        mock_glance_client().get_image.assert_called_once_with(fake_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_check_dependent_images_for_ari(self, mock_glance_client):
        fake_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image', 'ari',
                                  'ari', FAKE_ID)
        mock_glance_client().get_image.return_value = fake_image
        glance_adapter.check_dependent_images('fake_region', self.ctx,
                                              fake_image.id)
        mock_glance_client().get_image.assert_called_once_with(fake_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_check_dependent_images_for_ami(self, mock_glance_client):
        fake_ami_image = FakeAMIimage(0, 'False', 0, 'fake_image', 'ami',
                                      'ami', FAKE_KERNEL_ID,
                                      FAKE_RAMDISK_ID, FAKE_ID)
        fake_aki_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image',
                                      'aki', 'aki', FAKE_ID)
        fake_ari_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image',
                                      'ari', 'ari', FAKE_ID)

        mock_glance_client().get_image.side_effect = [
            fake_ami_image, fake_aki_image, fake_ari_image]
        dependent_images = glance_adapter.check_dependent_images(
            'fake_region', self.ctx, fake_ami_image.id)
        self.assertEqual(mock_glance_client().get_image.call_count, 3)
        expected_result = {
            'kernel_image': fake_aki_image,
            'ramdisk_image': fake_ari_image
        }
        self.assertEqual(dependent_images, expected_result)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_ami_image_without_dependent_images(self, mock_glance_client):
        fake_ami_image = FakeAMIimage(0, 'False', 0, 'fake_image', 'ami',
                                      'ami', None, None, FAKE_ID)
        mock_glance_client().get_image.side_effect = [
            fake_ami_image, None, None]
        self.assertRaises(exceptions.DependentImageNotFound,
                          glance_adapter.check_dependent_images,
                          'fake_region', self.ctx,
                          fake_ami_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_ami_image_with_wrong_aki_image(self, mock_glance_client):
        fake_ami_image = FakeAMIimage(0, 'False', 0, 'fake_image', 'ami',
                                      'ami', FAKE_KERNEL_ID,
                                      FAKE_RAMDISK_ID, FAKE_ID)
        fake_aki_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image',
                                      'aki', 'fake_aki', FAKE_ID)
        fake_ari_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image',
                                      'ari', 'ari', FAKE_ID)
        mock_glance_client().get_image.side_effect = [
            fake_ami_image, fake_aki_image, fake_ari_image]
        self.assertRaises(exceptions.DependentImageNotFound,
                          glance_adapter.check_dependent_images,
                          'fake_region', self.ctx,
                          fake_ami_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_ami_image_with_wrong_ari_image(self, mock_glance_client):
        fake_ami_image = FakeAMIimage(0, 'False', 0, 'fake_image', 'ami',
                                      'ami', FAKE_KERNEL_ID, FAKE_RAMDISK_ID,
                                      FAKE_ID)
        fake_aki_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image',
                                      'aki', 'aki', FAKE_ID)
        fake_ari_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image',
                                      'ari', 'fake_ari', FAKE_ID)
        mock_glance_client().get_image.side_effect = [
            fake_ami_image, fake_aki_image, fake_ari_image]
        self.assertRaises(exceptions.DependentImageNotFound,
                          glance_adapter.check_dependent_images,
                          'fake_region', self.ctx,
                          fake_ami_image.id)

    @patch('kingbird.drivers.openstack.glance_adapter.GlanceClient')
    def test_image_with_wrong_format_image(self, mock_glance_client):
        fake_image = FakeQCOW2Image(0, 'False', 0, 'fake_image', 'bare',
                                    'fake_format', FAKE_ID)
        mock_glance_client().get_image.return_value = fake_image
        self.assertRaises(exceptions.ImageFormatNotSupported,
                          glance_adapter.check_dependent_images,
                          'fake_region', self.ctx,
                          fake_image.id)
