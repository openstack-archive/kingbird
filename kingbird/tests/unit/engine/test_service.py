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

from kingbird.engine.listener import EngineManager
from kingbird.engine import service
from kingbird.tests import base
from oslo_config import cfg

CONF = cfg.CONF


class TestEngineService(base.KingbirdTestCase):
    def setUp(self):
        super(TestEngineService, self).setUp()

    def test_init(self):
        manager = EngineManager()
        engine_service = service.EngineService('127.0.0.1', 'engine',
                                               'topic-A', manager)
        self.assertIsNotNone(engine_service)


@mock.patch.object(service, 'EngineService')
def test_create_service(mock_engine):
    service.create_service()
    mock_engine().start.assert_called_once_with()


@mock.patch.object(service, 'EngineService')
@mock.patch.object(service, 'srv')
def test_serve(mock_srv, mock_engine):
    manager = EngineManager()
    engine_service = service.EngineService('127.0.0.1', 'engine',
                                           'topic-A', manager)
    service.serve(engine_service, 2)
    mock_srv.launch.assert_called_once_with(CONF, engine_service, workers=2)


@mock.patch.object(service, '_launcher')
def test_wait(mock_launcher):
    service.wait()
    mock_launcher.wait.assert_called_once_with()
