# Copyright (c) 2017 Ericsson AB.
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

found_id = False
admin_id = None
with open("/srv/salt/admin_tenant_details.txt", "r") as fopen:
    for data in fopen:
        if data.strip() == "id:":
            found_id = True
            continue
        if found_id:
            admin_id = data.strip()
            break
if found_id:
    print(admin_id)
