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


KBGroup = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help="Endpoint type of Kingbird service."),
    cfg.IntOpt('TIME_TO_SYNC',
               default=30,
               help="Maximum time to wait for a sync call to complete."),
    cfg.StrOpt('endpoint_url',
               default='http://127.0.0.1:8118/',
               help="Endpoint URL of Kingbird service."),
    cfg.StrOpt('api_version',
               default='v1.0',
               help="Api version of Kingbird service.")
]
