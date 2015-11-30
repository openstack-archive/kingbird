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

from mock import patch

from kingbird.common import endpoint_cache
from kingbird.tests import base

FAKE_REGION = 'fake_region'
FAKE_SERVICE = 'fake_service'
FAKE_URL = 'fake_url'


class EndpointCacheTest(base.KingbirdTestCase):
    def setUp(self):
        super(EndpointCacheTest, self).setUp()

    @patch.object(endpoint_cache.EndpointCache, '_get_endpoint_from_keystone')
    def test_get_endpoint(self, mock_method):
        mock_method.return_value = {FAKE_REGION: {FAKE_SERVICE: FAKE_URL}}
        cache = endpoint_cache.EndpointCache()
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         FAKE_URL)

    @patch.object(endpoint_cache.EndpointCache, '_get_endpoint_from_keystone')
    def test_get_endpoint_not_found(self, mock_method):
        mock_method.return_value = {FAKE_REGION: {FAKE_SERVICE: FAKE_URL}}
        cache = endpoint_cache.EndpointCache()
        self.assertEqual(cache.get_endpoint('another_fake_region',
                                            FAKE_SERVICE), '')
        self.assertEqual(cache.get_endpoint(FAKE_REGION,
                                            'another_fake_service'), '')

    @patch.object(endpoint_cache.EndpointCache, '_get_endpoint_from_keystone')
    def test_get_endpoint_retry(self, mock_method):
        cache = endpoint_cache.EndpointCache()
        mock_method.return_value = {
            'another_region': {FAKE_SERVICE: 'another_fake_url'}}
        self.assertEqual(cache.get_endpoint('another_region', FAKE_SERVICE),
                         'another_fake_url')

    @patch.object(endpoint_cache.EndpointCache, '_get_endpoint_from_keystone')
    def test_update_endpoint(self, mock_method):
        mock_method.return_value = {
            FAKE_REGION: {FAKE_SERVICE: FAKE_URL}}
        cache = endpoint_cache.EndpointCache()
        mock_method.return_value = {
            FAKE_REGION: {FAKE_SERVICE: 'another_fake_url'}}
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         FAKE_URL)
        cache.update_endpoints()
        self.assertEqual(cache.get_endpoint(FAKE_REGION, FAKE_SERVICE),
                         'another_fake_url')
