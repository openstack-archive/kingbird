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

from kingbird.drivers.openstack import cinder_v3
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

FAKE_LIMITS = {'absolute':
               {u'totalSnapshotsUsed': 15, u'maxTotalBackups': 10,
                u'maxTotalVolumeGigabytes': 1000, u'maxTotalSnapshots': 10,
                u'maxTotalBackupGigabytes': 1000,
                u'totalBackupGigabytesUsed': 0, u'maxTotalVolumes': 10,
                u'totalVolumesUsed': 25, u'totalBackupsUsed': 16,
                u'totalGigabytesUsed': 14
                }
               }

DISABLED_QUOTAS = ["floating_ips", "fixed_ips", "security_groups"]


class TestCinderClient(base.KingbirdTestCase):
    def setUp(self):
        super(TestCinderClient, self).setUp()
        self.ctx = utils.dummy_context()
        self.session = 'fake_session'
        self.project = 'fake_project'

    def test_init(self):
        ci_client = cinder_v3.CinderClient('fake_region', DISABLED_QUOTAS,
                                           self.session)
        self.assertIsNotNone(ci_client)
        self.assertIsInstance(ci_client.cinder,
                              cinderclient.v3.client.Client)

    @mock.patch.object(cinder_v3, 'client')
    def test_get_resource_usages(self, mock_cinderclient):
        mock_cinderclient.Client().limits.get().to_dict.\
            return_value = FAKE_LIMITS
        cinder = cinder_v3.CinderClient('fake_region', DISABLED_QUOTAS,
                                        self.session)
        total_cinder_usage = cinder.get_resource_usages(self.project)
        self.assertEqual(25, total_cinder_usage['volumes'])
        self.assertEqual(15, total_cinder_usage['snapshots'])
        self.assertEqual(14, total_cinder_usage['gigabytes'])
        self.assertEqual(16, total_cinder_usage['backups'])

    @mock.patch.object(cinder_v3, 'client')
    def test_update_quota_limits(self, mock_cinderclient):
        c_client = cinder_v3.CinderClient('fake_region', DISABLED_QUOTAS,
                                          self.session)
        new_quota = {'volumes': 4, 'snapshots': 3}
        c_client.update_quota_limits(self.project, **new_quota)

        mock_cinderclient.Client().quotas.update.assert_called_once_with(
            self.project, **new_quota)

    @mock.patch.object(cinder_v3, 'client')
    def test_delete_quota_limits(self, mock_cinderclient):
        c_client = cinder_v3.CinderClient('fake_region', DISABLED_QUOTAS,
                                          self.session)
        new_quota = {'volumes': 4, 'snapshots': 3}
        c_client.update_quota_limits(self.project, **new_quota)

        c_client.delete_quota_limits(self.project)

        mock_cinderclient.Client().quotas.delete.assert_called_once_with(
            self.project)
