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
from collections import Counter
import mock
from Queue import Queue
import uuid

from oslo_config import cfg

from kingbird.common import config
from kingbird.engine import quota_manager
from kingbird.tests import base
from kingbird.tests import utils

CONF = cfg.CONF
FAKE_PROJECT = 'fake_project'
FAKE_REGION = 'fake_region'
FAKE_ENGINE_ID = str(uuid.uuid4())
NOVA_USAGE = {'ram': 100, 'cores': '50'}
NEUTRON_USAGE = {'port': 10}
CINDER_USAGE = {'volumes': 18}
FAKE_REGION_DICT = {'region1': {'ram': 100},
                    'region2': {'ram': 200, 'volumes': 500}}
TOTAL_USAGE = {}
TOTAL_USAGE.update(NOVA_USAGE)
TOTAL_USAGE.update(NEUTRON_USAGE)
TOTAL_USAGE.update(CINDER_USAGE)
TASK_TYPE = 'quota_sync'


class TestQuotaManager(base.KingbirdTestCase):
    def setUp(self):
        super(TestQuotaManager, self).setUp()
        self.ctxt = utils.dummy_context()

    @mock.patch.object(quota_manager, 'endpoint_cache')
    @mock.patch.object(quota_manager, 'context')
    def test_init(self, mock_context, mock_endpoint):
        mock_context.get_admin_context.return_value = self.ctxt
        qm = quota_manager.QuotaManager()
        self.assertIsNotNone(qm)
        self.assertEqual('quota_manager', qm.service_name)
        self.assertEqual('localhost', qm.host)
        self.assertEqual(self.ctxt, qm.context)

    @mock.patch.object(quota_manager, 'context')
    @mock.patch.object(quota_manager.QuotaManager, 'quota_sync_for_project')
    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    @mock.patch.object(quota_manager, 'kingbird_lock')
    def test_periodic_balance_all(self, mock_kb_lock, mock_endpoint,
                                  mock_sdk, mock_quota_sync, mock_context):
        mock_context.get_admin_context.return_value = self.ctxt
        mock_sdk.OpenStackDriver().get_enabled_projects.return_value = \
            ['proj1']
        mock_kb_lock.sync_lock_acquire.return_value = True
        qm = quota_manager.QuotaManager()
        qm.periodic_balance_all(FAKE_ENGINE_ID)
        mock_quota_sync.assert_called_with('proj1')
        mock_kb_lock.sync_lock_release.assert_called_once_with(self.ctxt,
                                                               FAKE_ENGINE_ID,
                                                               TASK_TYPE)

    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_read_quota_usage(self, mock_endpoint,
                              mock_sdk):
        mock_sdk.OpenStackDriver().get_resource_usages.return_value = \
            NOVA_USAGE, NEUTRON_USAGE, CINDER_USAGE
        usage_queue = Queue()
        qm = quota_manager.QuotaManager()
        qm.read_quota_usage(FAKE_PROJECT, FAKE_REGION, usage_queue)
        actual_usage = usage_queue.get()
        self.assertEqual(actual_usage, {FAKE_REGION: TOTAL_USAGE})

    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_get_summation(self, mock_endpoint):
        expected_sum = Counter(dict(Counter(FAKE_REGION_DICT['region1'])
                               + Counter(FAKE_REGION_DICT['region2'])))
        qm = quota_manager.QuotaManager()
        actual_sum = qm.get_summation(FAKE_REGION_DICT)
        self.assertEqual(expected_sum, actual_sum)

    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_get_kingbird_project_limit(self, mock_endpoint,
                                        mock_db_api):
        config.register_options()
        qm = quota_manager.QuotaManager()
        mock_db_api.quota_get_all_by_project.return_value = {
            'project_id': FAKE_PROJECT, 'ram': 51000}
        actual_global_limit = qm._get_kingbird_project_limit(FAKE_PROJECT)
        # Assert kingbird limits from conf file
        self.assertEqual(CONF.kingbird_global_limit['quota_cores'],
                         actual_global_limit['cores'])
        self.assertEqual(CONF.kingbird_global_limit['quota_key_pairs'],
                         actual_global_limit['key_pairs'])
        self.assertEqual(CONF.kingbird_global_limit['quota_router'],
                         actual_global_limit['router'])
        self.assertEqual(CONF.kingbird_global_limit['quota_port'],
                         actual_global_limit['port'])
        self.assertEqual(CONF.kingbird_global_limit['quota_network'],
                         actual_global_limit['network'])
        self.assertEqual(CONF.kingbird_global_limit['quota_volumes'],
                         actual_global_limit['volumes'])
        self.assertEqual(CONF.kingbird_global_limit['quota_instances'],
                         actual_global_limit['instances'])
        self.assertEqual(CONF.kingbird_global_limit['quota_floatingip'],
                         actual_global_limit['floatingip'])
        self.assertEqual(CONF.kingbird_global_limit['quota_metadata_items'],
                         actual_global_limit['metadata_items'])
        self.assertEqual(CONF.kingbird_global_limit['quota_security_group'],
                         actual_global_limit['security_group'])
        self.assertEqual(CONF.kingbird_global_limit['quota_backups'],
                         actual_global_limit['backups'])
        # Assert Kingbird limit from db which is mocked
        self.assertEqual(51000, actual_global_limit['ram'])

    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_arrange_quotas_by_service_name(self, mock_endpoint):
        qm = quota_manager.QuotaManager()
        actual_arranged_quotas = qm._arrange_quotas_by_service_name(
            TOTAL_USAGE)
        self.assertEqual(CINDER_USAGE, actual_arranged_quotas['cinder'])
        self.assertEqual(NEUTRON_USAGE, actual_arranged_quotas['neutron'])
        self.assertEqual(NOVA_USAGE, actual_arranged_quotas['nova'])

    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_update_quota_limits(self, mock_endpoint,
                                 mock_sdk):
        qm = quota_manager.QuotaManager()
        qm.update_quota_limits(FAKE_PROJECT, TOTAL_USAGE, FAKE_REGION)
        mock_sdk.OpenStackDriver().write_quota_limits.assert_called_once_with(
            FAKE_PROJECT, TOTAL_USAGE)

    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager.QuotaManager,
                       'get_tenant_quota_usage_per_region')
    @mock.patch.object(quota_manager.QuotaManager,
                       'update_quota_limits')
    @mock.patch.object(quota_manager.QuotaManager,
                       '_get_kingbird_project_limit')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_quota_sync_for_project(self, mock_endpoint, mock_kb_limit,
                                    mock_update, mock_quota_usage,
                                    mock_os_client, mock_dbapi):
        mock_os_client.OpenStackDriver(
            ).get_all_regions_for_project.return_value = [FAKE_REGION]
        mock_quota_usage.return_value = {FAKE_REGION: TOTAL_USAGE}
        mock_kb_limit.return_value = {'ram': 100}
        qm = quota_manager.QuotaManager()
        qm.quota_sync_for_project(FAKE_PROJECT)
        expected_limit = {'cinder': CINDER_USAGE, 'nova': NOVA_USAGE,
                          'neutron': NEUTRON_USAGE}
        mock_update.assert_called_once_with(FAKE_PROJECT, expected_limit,
                                            FAKE_REGION)

    @mock.patch.object(quota_manager, 'Queue')
    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    @mock.patch.object(quota_manager.QuotaManager, 'read_quota_usage')
    def test_get_tenant_quota_usage_per_region(self, mock_quota_usage,
                                               mock_endpoint,
                                               mock_sdk, mock_queue):
        qm = quota_manager.QuotaManager()
        mock_sdk.OpenStackDriver().get_all_regions_for_project.return_value = \
            [FAKE_REGION]
        qm.get_tenant_quota_usage_per_region(FAKE_PROJECT)
        mock_quota_usage.assert_called_once_with(FAKE_PROJECT, FAKE_REGION,
                                                 mock_queue())

    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    @mock.patch.object(quota_manager.QuotaManager,
                       'get_tenant_quota_usage_per_region')
    def test_get_total_usage_for_tenant(self, mock_quota_usage,
                                        mock_endpoint, mock_db_api):
        qm = quota_manager.QuotaManager()
        qm.get_total_usage_for_tenant(FAKE_PROJECT)
        mock_quota_usage.assert_called_once_with(FAKE_PROJECT)

    @mock.patch.object(quota_manager, 'db_api')
    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager.QuotaManager,
                       'get_tenant_quota_usage_per_region')
    @mock.patch.object(quota_manager.QuotaManager,
                       'update_quota_limits')
    @mock.patch.object(quota_manager.QuotaManager,
                       '_get_kingbird_project_limit')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    def test_quota_sync_for_project_read_error(self, mock_endpoint,
                                               mock_kb_limit,
                                               mock_update,
                                               mock_quota_usage,
                                               mock_os_client, mock_dbapi):
        mock_os_client.OpenStackDriver(
            ).get_all_regions_for_project.return_value = [FAKE_REGION]
        mock_quota_usage.return_value = {}
        mock_kb_limit.return_value = {'ram': 100}
        qm = quota_manager.QuotaManager()
        qm.quota_sync_for_project(FAKE_PROJECT)
        mock_update.assert_not_called()

    @mock.patch.object(quota_manager.QuotaManager, 'quota_sync_for_project')
    @mock.patch.object(quota_manager, 'sdk')
    @mock.patch.object(quota_manager, 'endpoint_cache')
    @mock.patch.object(quota_manager, 'kingbird_lock')
    def test_periodic_balance_all_lock_fail(self, mock_kb_lock, mock_endpoint,
                                            mock_sdk, mock_quota_sync):
        mock_sdk.OpenStackDriver().get_enabled_projects.return_value = \
            ['proj1']
        mock_kb_lock.sync_lock_acquire.return_value = False
        qm = quota_manager.QuotaManager()
        qm.periodic_balance_all(FAKE_ENGINE_ID)
        mock_quota_sync.assert_not_called()
