# Copyright 2016 Ericsson AB.
# All Rights Reserved
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
CLI interface for kingbird management.
"""


import sys

from oslo_config import cfg
from oslo_db import options

from kingbird.db import api as api
from kingbird.db.sqlalchemy import api as db_api


def main(argv=None, config_files=None):
    get_engine = api.get_engine

    cfg.CONF(args=argv[2:],
             project='kingbird',
             default_config_files=config_files)

    options.cfg.set_defaults(options.database_opts,
                             sqlite_synchronous=False)
    options.set_defaults(cfg.CONF, connection=cfg.CONF.database.connection)
    engine = get_engine()
    db_api.db_sync(engine)
    engine.connect()


if __name__ == '__main__':
    config_file = sys.argv[1]
    main(argv=sys.argv, config_files=[config_file])
