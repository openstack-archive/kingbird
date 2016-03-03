# Copyright 2016 Ericsson AB
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

from kingbird.common import utils
from kingbird.tests import base


class TestUtils(base.KingbirdTestCase):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_get_batch_projects(self):
        fake_project_list = ['proj1', 'proj2', 'proj3', 'proj4',
                             'proj5', 'proj6', 'proj7']
        actual_project_list = utils.get_batch_projects(3, fake_project_list)
        self.assertEqual((fake_project_list[0], fake_project_list[1],
                          fake_project_list[2]), actual_project_list.next())
        self.assertEqual((fake_project_list[3], fake_project_list[4],
                          fake_project_list[5]), actual_project_list.next())
        self.assertEqual((fake_project_list[6], None, None),
                         actual_project_list.next())
