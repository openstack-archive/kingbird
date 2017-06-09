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

from kingbird.engine import image_sync_manager
from kingbird.tests import base
from kingbird.tests import utils

DEFAULT_FORCE = False
FAKE_USER_ID = 'user123'
FAKE_TARGET_REGION = 'fake_target_region'
FAKE_SOURCE_REGION = 'fake_source_region'
FAKE_RESOURCE_ID = 'fake_id'
FAKE_JOB_ID = utils.UUID1
FAKE_KERNEL_ID = utils.UUID2
FAKE_RAMDISK_ID = utils.UUID3
FAKE_ID = utils.UUID4
FAKE_RESULT = 'SUCCESS'
FAKE_RESULT_FAIL = 'FAILURE'
FAKE_RESOURCE = 'fake_image'


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


class TestImageSyncManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestImageSyncManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @patch('kingbird.engine.image_sync_manager.db_api')
    @patch('kingbird.engine.image_sync_manager.glance_adapter')
    @patch('kingbird.engine.image_sync_manager.GlanceClient')
    @patch('kingbird.engine.image_sync_manager.GlanceUpload')
    def test_ami_image_sync(self, mock_glance_upload, mock_glance_client,
                            mock_glance_adapter, mock_db_api):
        fake_ami_image = FakeAMIimage(0, 'False', 0, FAKE_RESOURCE, 'ami',
                                      'ami', FAKE_KERNEL_ID,
                                      FAKE_RAMDISK_ID, FAKE_ID)
        fake_aki_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image',
                                      'aki', 'aki', FAKE_ID)
        fake_ari_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image',
                                      'ari', 'ari', FAKE_ID)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_ami_image.id]
        expected_resources = {
            'kernel_image': fake_aki_image,
            'ramdisk_image': fake_ari_image
        }
        mock_glance_adapter.check_dependent_images.\
            return_value = expected_resources
        ism = image_sync_manager.ImageSyncManager()
        ism.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_glance_adapter.check_dependent_images.\
            assert_called_once_with(self.ctxt, FAKE_SOURCE_REGION,
                                    fake_ami_image.id)
        self.assertEqual(mock_glance_client().get_image_data.call_count, 3)
        self.assertEqual(mock_glance_client().create_image.call_count, 3)
        self.assertEqual(mock_glance_upload.call_count, 3)
        self.assertEqual(mock_glance_client().image_upload.call_count, 3)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, FAKE_RESULT)

    @patch('kingbird.engine.image_sync_manager.db_api')
    @patch('kingbird.engine.image_sync_manager.glance_adapter')
    @patch('kingbird.engine.image_sync_manager.GlanceClient')
    @patch('kingbird.engine.image_sync_manager.GlanceUpload')
    def test_qcow2_image_sync(self, mock_glance_upload, mock_glance_client,
                              mock_glance_adapter, mock_db_api):
        fake_qcow2_image = FakeQCOW2Image(0, 'False', 0, FAKE_RESOURCE, 'bare',
                                          'qcow2', FAKE_ID)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_qcow2_image.id]
        expected_resources = None
        mock_glance_adapter.check_dependent_images.\
            return_value = expected_resources
        ism = image_sync_manager.ImageSyncManager()
        ism.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_glance_adapter.check_dependent_images.\
            assert_called_once_with(self.ctxt, FAKE_SOURCE_REGION,
                                    fake_qcow2_image.id)
        self.assertEqual(mock_glance_client().get_image_data.call_count, 1)
        self.assertEqual(mock_glance_client().create_image.call_count, 1)
        self.assertEqual(mock_glance_upload.call_count, 1)
        self.assertEqual(mock_glance_client().image_upload.call_count, 1)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, FAKE_RESULT)

    @patch('kingbird.engine.image_sync_manager.db_api')
    @patch('kingbird.engine.image_sync_manager.glance_adapter')
    @patch('kingbird.engine.image_sync_manager.GlanceClient')
    @patch('kingbird.engine.image_sync_manager.GlanceUpload')
    def test_aki_image_sync(self, mock_glance_upload, mock_glance_client,
                            mock_glance_adapter, mock_db_api):
        fake_aki_image = FakeAKIimage(0, 'False', 0, 'fake_kernel_image',
                                      'aki', 'aki', FAKE_ID)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_aki_image.id]
        expected_resources = None
        mock_glance_adapter.check_dependent_images.\
            return_value = expected_resources
        ism = image_sync_manager.ImageSyncManager()
        ism.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_glance_adapter.check_dependent_images.\
            assert_called_once_with(self.ctxt, FAKE_SOURCE_REGION,
                                    fake_aki_image.id)
        self.assertEqual(mock_glance_client().get_image_data.call_count, 1)
        self.assertEqual(mock_glance_client().create_image.call_count, 1)
        self.assertEqual(mock_glance_upload.call_count, 1)
        self.assertEqual(mock_glance_client().image_upload.call_count, 1)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, FAKE_RESULT)

    @patch('kingbird.engine.image_sync_manager.db_api')
    @patch('kingbird.engine.image_sync_manager.glance_adapter')
    @patch('kingbird.engine.image_sync_manager.GlanceClient')
    @patch('kingbird.engine.image_sync_manager.GlanceUpload')
    def test_ari_image_sync(self, mock_glance_upload, mock_glance_client,
                            mock_glance_adapter, mock_db_api):
        fake_ari_image = FakeARIimage(0, 'False', 0, 'fake_ramdisk_image',
                                      'ari', 'ari', FAKE_ID)
        payload = dict()
        payload['target'] = [FAKE_TARGET_REGION]
        payload['force'] = DEFAULT_FORCE
        payload['source'] = FAKE_SOURCE_REGION
        payload['resources'] = [fake_ari_image.id]
        expected_resources = None
        mock_glance_adapter.check_dependent_images.\
            return_value = expected_resources
        ism = image_sync_manager.ImageSyncManager()
        ism.resource_sync(self.ctxt, FAKE_JOB_ID, payload)
        mock_glance_adapter.check_dependent_images.\
            assert_called_once_with(self.ctxt, FAKE_SOURCE_REGION,
                                    fake_ari_image.id)
        self.assertEqual(mock_glance_client().get_image_data.call_count, 1)
        self.assertEqual(mock_glance_client().create_image.call_count, 1)
        self.assertEqual(mock_glance_upload.call_count, 1)
        self.assertEqual(mock_glance_client().image_upload.call_count, 1)
        mock_db_api.resource_sync_status.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID)
        mock_db_api.sync_job_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID, FAKE_RESULT)

    @patch('kingbird.engine.image_sync_manager.db_api')
    def test_update_success_result_in_db(self, mock_db_api):
        ism = image_sync_manager.ImageSyncManager()
        ism.update_result_in_database(self.ctxt, FAKE_JOB_ID,
                                      FAKE_TARGET_REGION, FAKE_RESOURCE,
                                      True)
        mock_db_api.resource_sync_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID,
                                    FAKE_TARGET_REGION, FAKE_RESOURCE,
                                    FAKE_RESULT)

    @patch('kingbird.engine.image_sync_manager.db_api')
    def test_update_fail_result_in_db(self, mock_db_api):
        ism = image_sync_manager.ImageSyncManager()
        ism.update_result_in_database(self.ctxt, FAKE_JOB_ID,
                                      FAKE_TARGET_REGION, FAKE_RESOURCE,
                                      False)
        mock_db_api.resource_sync_update.\
            assert_called_once_with(self.ctxt, FAKE_JOB_ID,
                                    FAKE_TARGET_REGION, FAKE_RESOURCE,
                                    FAKE_RESULT_FAIL)
