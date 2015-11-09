# Copyright 2015 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import eventlet

if __name__ == "__main__":
    eventlet.monkey_patch()

import sys

from oslo_config import cfg
from oslo_log import log as logging

import logging as std_logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

from kingbird.common.i18n import _LI
from kingbird.common.i18n import _LW
from kingbird.jobworker import jwcfg
import kingbird.jobworker.jwservice as service


def main():
    jwcfg.init(sys.argv[1:])
    jwcfg.setup_logging()

    host = CONF.host
    workers = CONF.workers

    if workers < 1:
        LOG.warning(_LW("Wrong worker number, worker = %(workers)s"), workers)
        workers = 1

    LOG.info(_LI("Server on http://%(host)s with %(workers)s"),
             {'host': host, 'workers': workers})

    jwservice = service.create_service()
    service.serve(jwservice, cfg.CONF.workers)
    service.wait()

    LOG.info(_LI("Configuration:"))
    CONF.log_opt_values(LOG, std_logging.INFO)


if __name__ == '__main__':
    main()
