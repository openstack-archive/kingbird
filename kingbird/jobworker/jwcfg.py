# Copyright 2015 Huawei Technologies Co., Ltd.
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

"""
Routines for configuring kingbird, largely copy from Neutron
"""

import sys

from oslo_config import cfg
from oslo_log import log as logging

from kingbird.common import rpc

from kingbird.common.i18n import _
from kingbird.common.i18n import _LI


# from kingbird import policy
from kingbird.common import version

LOG = logging.getLogger(__name__)

common_opts = [
    cfg.StrOpt('host', default='kingbird.jwhost',
               help=_("The host name for RPC server")),
    cfg.IntOpt('workers', default=2,
               help=_("number of workers")),
    cfg.StrOpt('state_path',
               default='/var/lib/kingbird',
               deprecated_name='pybasedir',
               help="Top-level directory for maintaining kingbird's state"),
]


def init(args, **kwargs):
    # Register the configuration options
    cfg.CONF.register_opts(common_opts)

    # ks_session.Session.register_conf_options(cfg.CONF)
    # auth.register_conf_options(cfg.CONF)
    logging.register_options(cfg.CONF)

    cfg.CONF(args=args, project='kingbird.jobworker',
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)

    rpc.init(cfg.CONF)


def setup_logging():
    """Sets up the logging options for a log with supplied name."""
    product_name = "kingbird.jobworker"
    logging.setup(cfg.CONF, product_name)
    LOG.info(_LI("Logging enabled!"))
    LOG.info(_LI("%(prog)s version %(version)s"),
             {'prog': sys.argv[0],
              'version': version.version_info.release_string()})
    LOG.debug("command line: %s", " ".join(sys.argv))


def reset_service():
    # Reset worker in case SIGHUP is called.
    # Note that this is called only in case a service is running in
    # daemon mode.
    setup_logging()

    # TODO(joehuang) enforce policy later
    # policy.refresh()
