#    Copyright 2016 Ericsson AB
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

"""
File to store all the configurations
"""
from oslo_config import cfg


# Global nova quotas for all projects
nova_quotas = [
    cfg.IntOpt('quota_instances', default=10),
    cfg.IntOpt('quota_cores', default=20),
    cfg.IntOpt('quota_ram', default=50 * 1024),
    cfg.IntOpt('quota_floating_ips', default=10),
    cfg.IntOpt('quota_fixed_ips', default=-1),
    cfg.IntOpt('quota_metadata_items', default=128),
    cfg.IntOpt('quota_security_groups', default=10),
    cfg.IntOpt('quota_key_pairs', default=100),
]

# Global neutron quotas for all projects
neutron_quotas = [
    cfg.IntOpt('quota_network', default=10),
    cfg.IntOpt('quota_subnet', default=10),
    cfg.IntOpt('quota_port', default=50),
    cfg.IntOpt('quota_security_group', default=10),
    cfg.IntOpt('quota_router', default=10),
    cfg.IntOpt('quota_floatingip', default=50)
]

# Global cinder quotas for all projects
cinder_quotas = [
    cfg.IntOpt('quota_volumes', default=10),
    cfg.IntOpt('quota_snapshots', default=10),
    cfg.IntOpt('quota_consistencygroups', default=10),
    cfg.IntOpt('quota_gigabytes', default=1000),
    cfg.IntOpt('quota_backups', default=10),
    cfg.IntOpt('quota_backup_gigabytes', default=1000)
]

# The group stores Kingbird global limit for all the projects
default_quota_group = cfg.OptGroup(name='kingbird_global_limit',
                                   title='Global quota limit for all projects')


def list_opts():
    yield default_quota_group.name, nova_quotas
    yield default_quota_group.name, neutron_quotas
    yield default_quota_group.name, cinder_quotas


def register_options():
    for group, opts in list_opts():
        cfg.CONF.register_opts(opts, group=group)
