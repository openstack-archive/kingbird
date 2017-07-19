# Copyright 2016 Ericsson AB.
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


DEFAULT_QUOTAS = {
    u'metadata_items': 128, u'subnet': 10,
    u'floatingip': 50, u'gigabytes': 1000, u'backup_gigabytes': 1000,
    u'ram': 51200, u'floating_ips': 10, u'snapshots': 10,
    u'security_group_rule': 100,
    u'instances': 10, u'key_pairs': 100, u'volumes': 10, u'router': 10,
    u'security_group': 10, u'cores': 20, u'backups': 10, u'fixed_ips': -1,
    u'port': 50, u'security_groups': 10, u'network': 10
}

KEYPAIR_RESOURCE_TYPE = "keypair"

IMAGE_RESOURCE_TYPE = "image"

JOB_SUCCESS = "SUCCESS"

JOB_PROGRESS = "IN_PROGRESS"

JOB_ACTIVE = "active"

JOB_FAILURE = "FAILURE"
