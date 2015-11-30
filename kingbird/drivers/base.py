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

'''
Base class for all drivers.
'''

import abc
import six

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class DriverBase(object):

    six.add_metaclass(abc.ABCMeta)
    '''Base class for all drivers.'''

    def __init__(self, context):
        self.context = context

    @abc.abstractmethod
    def get_resource_usages(self, project_id):
        '''Collects resource usages for a given project

        :params: project_id
        :return: dictionary of corresponding resources with its usage
        '''

    @abc.abstractmethod
    def update_quota_limits(self, project_id, new_quota):
        '''Updates quota limits for a given project

        :params: project_id, dictionary with the quota limits to update
        :return: Nothing
        '''

    @abc.abstractmethod
    def delete_quota_limits(self, project_id):
        '''Delete quota limits for a given project

        :params: project_id
        :return: Nothing
        '''
