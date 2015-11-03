# Copyright (c) 2015 Huawei, Tech. Co,. Ltd.
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
#    copy and modify from Nova

"""Generic service base class for all workers that run on hosts."""

import os
import random
import sys

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service

import baserpc

from kingbird.common.i18n import _
from kingbird.common.i18n import _LE
from kingbird.common.i18n import _LI

from kingbird.common import context
from kingbird.common import rpc
from kingbird.common import version

LOG = logging.getLogger(__name__)

service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='Seconds between nodes reporting state to datastore'),
    cfg.BoolOpt('periodic_enable',
               default=True,
               help='Enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='Range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    ]

CONF = cfg.CONF
CONF.register_opts(service_opts)


class Service(service.Service):
    """Service object for binaries running on hosts.
    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    its state to the database services table.
    """

    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, serializer = None,
                 *args, **kwargs):
        super(Service, self).__init__()
        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager = manager
        self.rpc_server = None
        self.report_interval = report_interval
        self.periodic_enable = periodic_enable
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.periodic_interval_max = periodic_interval_max
        self.serializer = serializer
        self.saved_args, self.saved_kwargs = args, kwargs

    def start(self):
        ver_str = version.version_string_with_package()
        LOG.info(_LI('Starting %(topic)s node (version %(version)s)'),
                  {'topic': self.topic, 'version': ver_str})

        self.basic_config_check()
        self.manager.init_host()
        self.manager.pre_start_hook()

        LOG.debug(_("Creating RPC server for service %s"), self.topic)

        target = messaging.Target(topic=self.topic, server=self.host)

        endpoints = [
            self.manager,
            baserpc.BaseServerRPCAPI(self.manager.service_name)
        ]
        endpoints.extend(self.manager.additional_endpoints)

        self.rpc_server = rpc.get_server(target, endpoints, self.serializer)
        self.rpc_server.start()

        self.manager.post_start_hook()

        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            self.tg.add_dynamic_timer(self.periodic_tasks,
                                      initial_delay=initial_delay,
                                      periodic_interval_max=
                                      self.periodic_interval_max)

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, host=None, binary=None, topic=None, manager=None,
               report_interval=None, periodic_enable=None,
               periodic_fuzzy_delay=None, periodic_interval_max=None,
               serializer = None,):
        """Instantiates class and passes back application object.
        :param host: defaults to CONF.host
        :param binary: defaults to basename of executable
        :param topic: defaults to bin_name - 'nova-' part
        :param manager: defaults to CONF.<topic>_manager
        :param report_interval: defaults to CONF.report_interval
        :param periodic_enable: defaults to CONF.periodic_enable
        :param periodic_fuzzy_delay: defaults to CONF.periodic_fuzzy_delay
        :param periodic_interval_max: if set, the max time to wait between runs
        """
        if not host:
            host = CONF.host
        if not binary:
            binary = os.path.basename(sys.argv[0])
        if not topic:
            topic = binary.rpartition('kingbird-')[2]
        if not manager:
            manager_cls = ('%s_manager' %
                           binary.rpartition('kingbird-')[2])
            manager = CONF.get(manager_cls, None)
        if report_interval is None:
            report_interval = CONF.report_interval
        if periodic_enable is None:
            periodic_enable = CONF.periodic_enable
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.periodic_fuzzy_delay

        service_obj = cls(host, binary, topic, manager,
                          report_interval=report_interval,
                          periodic_enable=periodic_enable,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          periodic_interval_max=periodic_interval_max,
                          serializer=serializer)

        return service_obj

    def kill(self):
        self.stop()

    def stop(self):
        try:
            self.rpc_server.stop()
            self.rpcserver.wait()
        except Exception:
            pass

        try:
            self.manager.cleanup_host()
        except Exception:
            LOG.exception(_LE('Service error occurred during cleanup_host'))
            pass

        super(Service, self).stop()

    def periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        ctxt = context.get_admin_context()
        return self.manager.periodic_tasks(ctxt, raise_on_error=raise_on_error)

    def basic_config_check(self):
        """Perform basic config checks before starting processing."""
        # Make sure the tempdir exists and is writable
        # try:
        #    with utils.tempdir():
        #        pass
        # except Exception as e:
        #    LOG.error(_LE('Temporary directory is invalid: %s'), e)
        #    sys.exit(1)
