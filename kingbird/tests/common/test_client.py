# Copyright 2015 Huawei Technologies Co., Ltd.
# All Rights Reserved
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

from kingbird.common import client
from kingbird.tests import base

FAKE_REGION = 'fake_region'
FAKE_SERVICE = 'fake_service'
FAKE_URL = 'fake_url'


class EndpointCacheTest(base.TestCase):
    def setUp(self):
        super(EndpointCacheTest, self).setUp()
        client.EndpointCache._get_endpoint_from_keystone = mock.Mock()
        client.EndpointCache._get_endpoint_from_keystone.return_value = {
            FAKE_REGION: {FAKE_SERVICE: FAKE_URL}}

    def test_get_endpoint(self):
        cache = client.EndpointCache()
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         FAKE_URL)

    def test_get_endpoint_not_found(self):
        cache = client.EndpointCache()
        self.assertEqual(cache.get_endpoint('another_fake_region',
                                            FAKE_SERVICE), '')
        self.assertEqual(cache.get_endpoint(FAKE_REGION,
                                            'another_fake_service'), '')

    def test_get_endpoint_retry(self):
        cache = client.EndpointCache()
        client.EndpointCache._get_endpoint_from_keystone.return_value = {
            'another_region': {FAKE_SERVICE: 'another_fake_url'}}
        self.assertEqual(cache.get_endpoint('another_region', FAKE_SERVICE),
                         'another_fake_url')

    def test_update_endpoint(self):
        cache = client.EndpointCache()
        client.EndpointCache._get_endpoint_from_keystone.return_value = {
            FAKE_REGION: {FAKE_SERVICE: 'another_fake_url'}}
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         FAKE_URL)
        cache.update_endpoints()
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         'another_fake_url')
