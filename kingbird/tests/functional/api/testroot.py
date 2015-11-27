# Copyright (c) 2015 Huawei Technologies Co., Ltd.
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

import mock
from mock import patch

import pecan
from pecan.configuration import set_config
from pecan.testing import load_test_app

from oslo_config import cfg
from oslo_config import fixture as fixture_config
from oslo_serialization import jsonutils
from oslo_utils import uuidutils

from kingbird.api import apicfg
from kingbird.api.controllers import helloworld
from kingbird.common import rpc
from kingbird.jobdaemon import jdrpcapi
from kingbird.tests import base


OPT_GROUP_NAME = 'keystone_authtoken'
cfg.CONF.import_group(OPT_GROUP_NAME, "keystonemiddleware.auth_token")


def fake_say_hello_world_call(self, ctxt, payload):
    info_text = "say_hello_world_call, payload: %s" % payload
    return {'jobdaemon': info_text}


def fake_say_hello_world_cast(self, ctxt, payload):
    info_text = "say_hello_world_cast, payload: %s" % payload
    return {'jobdaemon': info_text}


def fake_delete_response(self, context):
    resp = jsonutils.dumps(context.to_dict())
    return resp


class KBFunctionalTest(base.TestCase):

    def setUp(self):
        super(KBFunctionalTest, self).setUp()

        self.addCleanup(set_config, {}, overwrite=True)

        apicfg.test_init()

        self.CONF = self.useFixture(fixture_config.Config()).conf

        # self.setup_messaging(self.CONF)
        self.CONF.set_override('auth_strategy', 'noauth')

        self.app = self._make_app()

    def _make_app(self, enable_acl=False):
        self.config = {
            'app': {
                'root': 'kingbird.api.controllers.root.RootController',
                'modules': ['kingbird.api'],
                'enable_acl': enable_acl,
                'errors': {
                    400: '/error',
                    '__force_dict__': True
                }
            },
        }

        return load_test_app(self.config)

    def tearDown(self):
        super(KBFunctionalTest, self).tearDown()
        pecan.set_config({}, overwrite=True)


class TestRootController(KBFunctionalTest):
    """Test version listing on root URI."""

    def test_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_int, 200)
        json_body = jsonutils.loads(response.body)
        versions = json_body.get('versions')
        self.assertEqual(1, len(versions))

    def _test_method_returns_405(self, method):
        api_method = getattr(self.app, method)
        response = api_method('/', expect_errors=True)
        self.assertEqual(response.status_int, 405)

    def test_post(self):
        self._test_method_returns_405('post')

    def test_put(self):
        self._test_method_returns_405('put')

    def test_patch(self):
        self._test_method_returns_405('patch')

    def test_delete(self):
        self._test_method_returns_405('delete')

    def test_head(self):
        self._test_method_returns_405('head')


class TestV1Controller(KBFunctionalTest):

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_get(self):
        response = self.app.get('/v1.0')
        self.assertEqual(response.status_int, 200)
        json_body = jsonutils.loads(response.body)
        version = json_body.get('version')
        self.assertEqual('1.0', version)

        links = json_body.get('links')
        v1_link = links[0]
        helloworld_link = links[1]
        self.assertEqual('self', v1_link['rel'])
        self.assertEqual('helloworld', helloworld_link['rel'])

    def _test_method_returns_405(self, method):
        api_method = getattr(self.app, method)
        response = api_method('/v1.0', expect_errors=True)
        self.assertEqual(response.status_int, 405)

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_post(self):
        self._test_method_returns_405('post')

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_put(self):
        self._test_method_returns_405('put')

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_patch(self):
        self._test_method_returns_405('patch')

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_delete(self):
        self._test_method_returns_405('delete')

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_head(self):
        self._test_method_returns_405('head')


class TestHelloworld(KBFunctionalTest):

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_get(self):
        response = self.app.get('/v1.0/helloworld')
        self.assertEqual(response.status_int, 200)
        self.assertIn('hello world message for', response)

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_post(self):
        response = self.app.post_json('/v1.0/helloworld',
                                      headers={'X-Tenant-Id': 'tenid'})
        self.assertEqual(response.status_int, 200)
        self.assertIn('## post call ##', response)
        self.assertIn('jobdaemon', response)

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_put(self):
        response = self.app.put_json('/v1.0/helloworld',
                                     headers={'X-Tenant-Id': 'tenid'})
        self.assertEqual(response.status_int, 200)
        self.assertIn('## put call ##', response)
        self.assertIn('jobdaemon', response)

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_delete(self):
        response = self.app.delete('/v1.0/helloworld',
                                   headers={'X-Tenant-Id': 'tenid'})
        self.assertEqual(response.status_int, 200)
        self.assertIn('cast example', response)
        self.assertIn('check the log produced by jobdaemon', response)


class TestHelloworldContext(KBFunctionalTest):

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    @patch.object(helloworld.HelloWorldController, '_delete_response',
                  new=fake_delete_response)
    def test_context_set_in_request(self):
        response = self.app.delete('/v1.0/helloworld',
                                   headers={'X_Auth_Token': 'a-token',
                                            'X_TENANT_ID': 't-id',
                                            'X_USER_ID': 'u-id',
                                            'X_USER_NAME': 'u-name',
                                            'X_PROJECT_NAME': 't-name',
                                            'X_DOMAIN_ID': 'domainx',
                                            'X_USER_DOMAIN_ID': 'd-u',
                                            'X_PROJECT_DOMAIN_ID': 'p_d',
                                            })
        json_body = jsonutils.loads(response.body)
        self.assertIn('a-token', json_body)
        self.assertIn('t-id', json_body)
        self.assertIn('u-id', json_body)
        self.assertIn('u-name', json_body)
        self.assertIn('t-name', json_body)
        self.assertIn('domainx', json_body)
        self.assertIn('d-u', json_body)
        self.assertIn('p_d', json_body)


class TestErrors(KBFunctionalTest):

    def test_404(self):
        response = self.app.get('/assert_called_once', expect_errors=True)
        self.assertEqual(response.status_int, 404)

    @patch.object(rpc, 'get_client', new=mock.Mock())
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_call',
                  new=fake_say_hello_world_call)
    @patch.object(jdrpcapi.JobDaemonAPI, 'say_hello_world_cast',
                  new=fake_say_hello_world_cast)
    def test_bad_method(self):
        response = self.app.patch('/v1.0/helloworld/123.json',
                                  expect_errors=True)
        self.assertEqual(response.status_int, 405)


class TestRequestID(KBFunctionalTest):

    def test_request_id(self):
        response = self.app.get('/')
        self.assertIn('x-openstack-request-id', response.headers)
        self.assertTrue(
            response.headers['x-openstack-request-id'].startswith('req-'))
        id_part = response.headers['x-openstack-request-id'].split('req-')[1]
        self.assertTrue(uuidutils.is_uuid_like(id_part))


class TestKeystoneAuth(KBFunctionalTest):

    def setUp(self):
        super(KBFunctionalTest, self).setUp()

        self.addCleanup(set_config, {}, overwrite=True)

        apicfg.test_init()

        self.CONF = self.useFixture(fixture_config.Config()).conf

        cfg.CONF.set_override('auth_strategy', 'keystone')

        self.app = self._make_app()

    def test_auth_enforced(self):
        response = self.app.get('/', expect_errors=True)
        self.assertEqual(response.status_int, 401)
