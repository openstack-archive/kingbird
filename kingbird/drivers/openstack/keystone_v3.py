#   Copyright 2012-2013 OpenStack Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

from oslo_utils import importutils

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client

from kingbird.common import exceptions
from kingbird.drivers import base

# Ensure keystonemiddleware options are imported
importutils.import_module('keystonemiddleware.auth_token')


class KeystoneClient(base.DriverBase):
    '''Keystone V3 driver.'''

    def __init__(self, **kwargs):
        try:
            auth = v3.Password(
                auth_url=kwargs['auth_url'],
                username=kwargs['user_name'],
                password=kwargs['password'],
                project_name=kwargs['tenant_name'],
                project_domain_name=kwargs['project_domain'],
                user_domain_name=kwargs['user_domain'])
            sess = session.Session(auth=auth)
            self.keystone_client = client.Client(session=sess)
            self.services_list = self.keystone_client.services.list()
        except exceptions.HttpException:
            raise

    def get_enabled_projects(self):
        try:
            return [current_project.id for current_project in
                    self.keystone.projects.list() if current_project.enabled]
        except exceptions.HttpException:
            raise

    def is_service_enabled(self, service):
        try:
            for current_service in self.services_list:
                if service in current_service.type:
                    return True
            return False
        except exceptions.HttpException:
            raise
