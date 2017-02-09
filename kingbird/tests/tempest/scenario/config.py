# Copyright 2016 Ericsson AB
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
"""Configurations for Kingbird Tempest Plugin."""

from oslo_config import cfg
from tempest import config  # noqa

service_option = cfg.BoolOpt('kingbird',
                             default=True,
                             help="Whether or not kingbird is expected to be "
                                  "available")

kb_group = cfg.OptGroup(
    name="kingbird",
    title="kingbird configuration options")

KBGroup = [
    cfg.StrOpt(name='endpoint_type',
               default='publicURL',
               help="Endpoint type of Kingbird service."),
    cfg.IntOpt(name='TIME_TO_SYNC',
               default=60,
               help="Maximum time to wait for a sync call to complete."),
    cfg.StrOpt(name='endpoint_url',
               default='http://127.0.0.1:8118/',
               help="Endpoint URL of Kingbird service."),
    cfg.StrOpt(name='api_version',
               default='v1.0',
               help="Api version of Kingbird service.")
]
