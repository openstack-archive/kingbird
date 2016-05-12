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

import cinderclient
import mock

from kingbird.drivers.openstack import cinder_v2
from kingbird.tests import base
from kingbird.tests import utils


class Volume(object):
    def __init__(self, id, size):
        self.id = id
        self.size = size


class VolumeSnapshot(object):
    def __init__(self, volume_id):
        self.volume_id = volume_id


class VolumeBackup(object):
    def __init__(self, volume_id):
        self.volume_id = volume_id


volumes = [Volume("9fc1c259-1d66-470f-8525-313696d1ad46", 20),
           Volume("7f505069-ad68-48c3-a09f-16d7014ec707", 15)]

snapshots = [VolumeSnapshot(volumes[0].id)]

backups = [VolumeBackup(volumes[0].id),
           VolumeBackup(volumes[0].id),
           VolumeBackup(volumes[1].id)]
DISABLED_QUOTAS = ["floating_ips", "fixed_ips", "security_groups"]


class TestCinderClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestCinderClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.session = 'fake_session'
        self.project = 'fake_project'

    def test_init(self):
        ci_client = cinder_v2.CinderClient('fake_region', DISABLED_QUOTAS,
                                           self.session)
        self.assertIsNotNone(ci_client)
        self.assertIsInstance(ci_client.cinder,
                              cinderclient.v2.client.Client)

    @mock.patch.object(cinder_v2, 'client')
    def test_get_resource_usages(self, mock_cinderclient):
        mock_cinderclient.Client().volumes.list.return_value = volumes
        mock_cinderclient.Client().volume_snapshots.list.return_value = \
            snapshots
        mock_cinderclient.Client().backups.list.return_value = \
            backups
        cinder = cinder_v2.CinderClient('fake_region', DISABLED_QUOTAS,
                                        self.session)
        total_cinder_usage = cinder.get_resource_usages(self.project)
        self.assertEqual(2, total_cinder_usage['volumes'])
        self.assertEqual(1, total_cinder_usage['snapshots'])
        self.assertEqual(35, total_cinder_usage['gigabytes'])
        self.assertEqual(3, total_cinder_usage['backups'])

    @mock.patch.object(cinder_v2, 'client')
    def test_update_quota_limits(self, mock_cinderclient):
        c_client = cinder_v2.CinderClient('fake_region', DISABLED_QUOTAS,
                                          self.session)
        new_quota = {'volumes': 4, 'snapshots': 3}
        c_client.update_quota_limits(self.project, **new_quota)

        mock_cinderclient.Client().quotas.update.assert_called_once_with(
            self.project, **new_quota)

    @mock.patch.object(cinder_v2, 'client')
    def test_delete_quota_limits(self, mock_cinderclient):
        c_client = cinder_v2.CinderClient('fake_region', DISABLED_QUOTAS,
                                          self.session)
        new_quota = {'volumes': 4, 'snapshots': 3}
        c_client.update_quota_limits(self.project, **new_quota)

        c_client.delete_quota_limits(self.project)

        mock_cinderclient.Client().quotas.delete.assert_called_once_with(
            self.project)
