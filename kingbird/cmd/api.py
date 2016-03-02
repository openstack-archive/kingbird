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

# Much of this module is based on the work of the Ironic team
# see http://git.openstack.org/cgit/openstack/ironic/tree/ironic/cmd/api.py


import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import wsgi

import logging as std_logging

from kingbird.api import api_config
from kingbird.api import app

from kingbird.common import config
from kingbird.common.i18n import _LI
from kingbird.common.i18n import _LW

CONF = cfg.CONF
config.register_options()
LOG = logging.getLogger('kingbird.api')


def main():
    api_config.init(sys.argv[1:])
    api_config.setup_logging()
    application = app.setup_app()

    host = CONF.bind_host
    port = CONF.bind_port
    workers = CONF.api_workers

    if workers < 1:
        LOG.warning(_LW("Wrong worker number, worker = %(workers)s"), workers)
        workers = 1

    LOG.info(_LI("Server on http://%(host)s:%(port)s with %(workers)s"),
             {'host': host, 'port': port, 'workers': workers})

    service = wsgi.Server(CONF, "Kingbird", application, host, port)

    app.serve(service, CONF, workers)

    LOG.info(_LI("Configuration:"))
    CONF.log_opt_values(LOG, std_logging.INFO)

    app.wait()


if __name__ == '__main__':
    main()
