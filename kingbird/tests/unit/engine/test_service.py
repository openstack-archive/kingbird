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

from kingbird.engine import scheduler
from kingbird.engine import service
from kingbird.tests import base
from kingbird.tests import utils
from oslo_config import cfg

CONF = cfg.CONF


class TestEngineService(base.KingbirdTestCase):
    def setUp(self):
        super(TestEngineService, self).setUp()
        self.tenant_id = 'fake_admin'
        self.thm = scheduler.ThreadGroupManager()
        self.context = utils.dummy_context(user='test_user',
                                           tenant=self.tenant_id)
        self.service_obj = service.EngineService('kingbird',
                                                 'kingbird-engine')

    def test_init(self):
        self.assertEqual(self.service_obj.host, 'localhost')
        self.assertEqual(self.service_obj.topic, 'kingbird-engine')
        self.assertEqual(self.service_obj.periodic_enable,
                         CONF.scheduler.periodic_enable)
        self.assertEqual(self.service_obj.periodic_interval,
                         CONF.scheduler.periodic_interval)

    def test_init_tgm(self):
        self.service_obj.init_tgm()
        self.assertIsNotNone(self.service_obj.TG)

    @mock.patch.object(service, 'QuotaManager')
    def test_init_qm(self, mock_quota_manager):
        self.service_obj.init_qm()
        self.assertIsNotNone(self.service_obj.qm)

    @mock.patch.object(service, 'QuotaManager')
    @mock.patch.object(service, 'rpc_messaging')
    def test_start(self, mock_rpc, mock_quota_manager):
        self.service_obj.start()
        mock_rpc.get_rpc_server.assert_called_once_with(
            self.service_obj.target, self.service_obj)
        mock_rpc.get_rpc_server().start.assert_called_once_with()

    @mock.patch.object(service, 'QuotaManager')
    def test_periodic_balance_all(self, mock_quota_manager):
        self.service_obj.init_tgm()
        self.service_obj.init_qm()
        self.service_obj.periodic_balance_all(self.service_obj.engine_id)
        mock_quota_manager().periodic_balance_all.\
            assert_called_once_with(self.service_obj.engine_id)

    @mock.patch.object(service, 'QuotaManager')
    def test_get_total_usage_for_tenant(self, mock_quota_manager):
        self.service_obj.init_tgm()
        self.service_obj.init_qm()
        self.service_obj.get_total_usage_for_tenant(
            self.context, self.tenant_id)
        mock_quota_manager().get_total_usage_for_tenant.\
            assert_called_once_with(self.tenant_id)

    @mock.patch.object(service, 'QuotaManager')
    def test_quota_sync_for_project(self, mock_quota_manager):
        self.service_obj.init_tgm()
        self.service_obj.init_qm()
        self.service_obj.quota_sync_for_project(
            self.context, self.tenant_id)
        mock_quota_manager().quota_sync_for_project.\
            assert_called_once_with(self.tenant_id)

    @mock.patch.object(service, 'QuotaManager')
    @mock.patch.object(service, 'rpc_messaging')
    def test_stop_rpc_server(self, mock_rpc, mock_quota_manager):
        self.service_obj.start()
        self.service_obj._stop_rpc_server()
        mock_rpc.get_rpc_server().stop.assert_called_once_with()

    @mock.patch.object(service, 'QuotaManager')
    @mock.patch.object(service, 'rpc_messaging')
    def test_stop(self, mock_rpc, mock_quota_manager):
        self.service_obj.start()
        self.service_obj.stop()
        mock_rpc.get_rpc_server().stop.assert_called_once_with()
