# Copyright (c) 2015 Ericsson AB.
# All Rights Reserved.
#
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

from kingbird.objects import base as obj_base
from kingbird.tests import base

from oslo_versionedobjects import fields as obj_fields


class TestBaseObject(base.KingbirdTestCase):
    def test_base_class(self):
        obj = obj_base.KingbirdObject()
        self.assertEqual(obj_base.KingbirdObject.OBJ_PROJECT_NAMESPACE,
                         obj.OBJ_PROJECT_NAMESPACE)
        self.assertEqual(obj_base.KingbirdObject.VERSION,
                         obj.VERSION)

    @mock.patch.object(obj_base.KingbirdObject, "obj_reset_changes")
    def test_from_db_object(self, mock_obj_reset_ch):
        class TestKingbirdObject(obj_base.KingbirdObject,
                                 obj_base.VersionedObjectDictCompat):
            fields = {
                "key1": obj_fields.StringField(),
                "key2": obj_fields.StringField(),
            }

        obj = TestKingbirdObject()
        context = mock.Mock()
        db_obj = {
            "key1": "value1",
            "key2": "value2",
        }
        res = obj_base.KingbirdObject._from_db_object(context, obj, db_obj)
        self.assertIsNotNone(res)
        self.assertEqual("value1", obj["key1"])
        self.assertEqual("value2", obj["key2"])
        self.assertEqual(obj._context, context)
        mock_obj_reset_ch.assert_called_once_with()

    def test_from_db_object_none(self):
        obj = obj_base.KingbirdObject()
        db_obj = None
        context = mock.Mock()

        res = obj_base.KingbirdObject._from_db_object(context, obj, db_obj)
        self.assertIsNone(res)
