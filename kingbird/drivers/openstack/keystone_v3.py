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

from kingbird.common import exceptions
from kingbird.drivers import base

# Ensure keystonemiddleware options are imported
importutils.import_module('keystonemiddleware.auth_token')


class KeystoneClient(base.DriverBase):
    '''Keystone V3 driver.'''

    def __init__(self, client):
        self.keystone = client

    def get_enabled_projects(self):
        try:
            return [current_project.id for current_project in
                    self.keystone.projects.list() if current_project.enabled]
        except exceptions.HttpException as ex:
            raise ex

    def get_regions(self):
        '''returns lists of cached regions'''
        pass
