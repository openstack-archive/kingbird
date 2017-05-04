# Copyright 2017 Ericsson AB.

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
from oslo_log import log

from kingbird.common import exceptions

from glanceclient import Client

LOG = log.getLogger(__name__)
API_VERSION = '2'


class GlanceClient(object):
    '''Glance V2 driver.'''
    def __init__(self, endpoint, context):
        try:
            LOG.info('Creating Glance Object')
            params = dict()
            params['identity_headers'] = self.generate_identity_headers(
                context)
            self.glance_client = Client(str(API_VERSION), endpoint, **params)
        except exceptions.ServiceUnavailable:
            raise

    def generate_identity_headers(self, context, status='Confirmed'):
        return {
            'X-Auth-Token': getattr(context, 'auth_token', None),
            'X-User-Id': getattr(context, 'user', None),
            'X-Tenant-Id': getattr(context, 'project', None),
            'X-Roles': getattr(context, 'roles', []),
            'X-Identity-Status': status,
        }
