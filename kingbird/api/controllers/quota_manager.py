# Copyright (c) 2016 Ericsson AB
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

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import pecan
from pecan import expose
from pecan import request
from pecan import rest

from kingbird.common import context as cntx
from kingbird.common import exceptions
from kingbird.common import rpc
from kingbird.common.serializer import KingbirdSerializer as Serializer
from kingbird.common import topics
from kingbird.db.sqlalchemy import api as db_api

CONF = cfg.CONF

rpcapi_cap_opt = cfg.StrOpt('kb-engine',
                            help='Set a version cap for messages sent to'
                                 'kb-engine services. If you plan to do a'
                                 'live upgrade from an old version to a'
                                 'newer version, you should set this option'
                                 'to the old version before beginning the'
                                 'live upgrade procedure. Only upgrading'
                                 'to the next version is supported, so you'
                                 'cannot skip a release for the live upgrade'
                                 'procedure.')
CONF.register_opt(rpcapi_cap_opt, 'upgrade_levels')

LOG = logging.getLogger(__name__)


class QuotaManagerController(rest.RestController):

    VERSION_ALIASES = {
        'mitaka': '1.0',
    }

    def __init__(self, *args, **kwargs):
        super(QuotaManagerController, self).__init__(*args, **kwargs)
        target = messaging.Target(topic=topics.TOPIC_KB_ENGINE, version='1.0')
        upgrade_level = CONF.upgrade_levels.kb_engine
        version_cap = 1.0
        if upgrade_level == 'auto':
            version_cap = self._determine_version_cap(target)
        else:
            version_cap = self.VERSION_ALIASES.get(upgrade_level,
                                                   upgrade_level)
        serializer = Serializer()
        self.client = rpc.get_client(target,
                                     version_cap=version_cap,
                                     serializer=serializer)

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self, **arg):
        if pecan.request.method != 'GET':
            pecan.abort(405)

        context = cntx.get_admin_context()
        if context.is_admin:
            if 'project_id' in arg:
                project_id = arg['project_id']
            else:
                pecan.abort(404)
            try:
                if 'resource' in arg:
                    result = db_api.quota_get(context, **arg)
                    result = {'project_id': result.project_id,
                              result.resource: result.hard_limit}
                else:
                    result = db_api.quota_get_all_by_project(
                        context, project_id)
            except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)
            return result
        else:
            return {'Non admin call for index with project': arg}

    @index.when(method='PUT', template='json')
    def put(self):
        updated_quota = []
        context = cntx.get_admin_context()
        if not request.body:
            pecan.abort(404)
        payload = eval(request.body)
        try:
            for project, resources in payload.iteritems():
                for resource, limit in resources.iteritems():
                    result = db_api.quota_update(
                        context,
                        project_id=project,
                        resource=resource,
                        limit=limit)
                    result = {'project_id': result.project_id,
                              result.resource: result.hard_limit}
                    updated_quota.append(result)
        except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)
        return {'Quota Updated': updated_quota}

    @index.when(method='POST', template='json')
    def post(self):
        quota = []
        context = cntx.get_admin_context()
        if not request.body:
            pecan.abort(404)
        payload = eval(request.body)
        try:
            for project, resources in payload.iteritems():
                for resource, limit in resources.iteritems():
                    result = db_api.quota_create(
                        context,
                        project_id=project,
                        resource=resource,
                        limit=limit)
                    result = {'project_id': result.project_id,
                              result.resource: result.hard_limit}
                    quota.append(result)
        except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)
        return {'Quota Created': quota}

    @index.when(method='delete', template='json')
    def delete(self):
        context = cntx.get_admin_context()
        if not request.body:
            pecan.abort(404)
        payload = eval(request.body)
        try:
            for project, resources in payload.iteritems():
                if resources == 'all':
                    db_api.quota_destroy_all(context, project)
                else:
                    for resource in resources:
                        db_api.quota_destroy(context, project, resource)
        except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)
