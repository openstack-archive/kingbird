# Copyright (c) 2015 Ericsson AB
# All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
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

from kingbird.common import exceptions
from kingbird.db.sqlalchemy import api as db_api
from kingbird.tests import base
from kingbird.tests import utils

UUID1 = utils.UUID1
UUID2 = utils.UUID2
UUID3 = utils.UUID3


class DBAPIQuotaTest(base.KingbirdDbTestCase):
    def setUp(self):
        super(DBAPIQuotaTest, self).setUp()
        self.ctx = utils.dummy_context()

    def test_create_quota_limit(self):
        project_id = UUID2
        resource = 'cores'
        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        cores_limit = db_api.quota_get(self.ctx, project_id, resource)
        self.assertIsNotNone(cores_limit)
        self.assertEqual(15, cores_limit.hard_limit)

    def test_update_quota_limit(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        updated = db_api.quota_update(self.ctx, project_id, resource, 10)
        self.assertIsNotNone(updated)

        updated_limit = db_api.quota_get(self.ctx, project_id, resource)
        self.assertEqual(10, updated_limit.hard_limit)

    def test_delete_quota_limit(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        db_api.quota_destroy(self.ctx, project_id, resource)

        self.assertRaises(exceptions.ProjectQuotaNotFound,
                          db_api.quota_get,
                          self.ctx, project_id, resource)

    def test_quota_get_by_project(self):
        project_id = UUID2
        resource = 'cores'

        limit = self.create_quota_limit(self.ctx, project_id=project_id,
                                        resource=resource, limit=15)
        self.assertIsNotNone(limit)

        by_project = db_api.quota_get_all_by_project(self.ctx, project_id)
        self.assertIsNotNone(by_project)
        self.assertEqual(project_id, by_project['project_id'])
