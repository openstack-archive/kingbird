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

import collections
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import pecan
from pecan import expose
from pecan import request

import restcomm

from kingbird.common import exceptions
from kingbird.common import rpc
from kingbird.common.serializer import KingbirdSerializer as Serializer
from kingbird.common import topics
from kingbird.db.sqlalchemy import api as db_api

CONF = cfg.CONF

rpc_api_cap_opt = cfg.StrOpt('kb-engine',
                             help='Set a version cap for messages sent to'
                                  'kb-engine services. If you plan to do a'
                                  'live upgrade from an old version to a'
                                  'newer version, you should set this option'
                                  'to the old version before beginning the'
                                  'live upgrade procedure. Only upgrading'
                                  'to the next version is supported, so you'
                                  'cannot skip a release for the live upgrade'
                                  'procedure.')
CONF.register_opt(rpc_api_cap_opt, 'upgrade_levels')

LOG = logging.getLogger(__name__)


class QuotaManagerController(object):
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
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project_id, resource=None):
        quota = collections.defaultdict(dict)
        context = restcomm.extract_context_from_environ()
        if context.is_admin:
            try:
                if project_id == 'defaults':
                    # Get default quota limits from conf file
                    result = collections.defaultdict(dict)
                    for resource, limit in \
                        CONF.kingbird_global_limit.iteritems():
                            result[resource.replace('quota_', '')] = limit
                else:
                    # Get quota limits for all the resources for a project
                    result = db_api.quota_get_all_by_project(
                        context, project_id)
                quota['quota_set'] = result
                return quota
            except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)
        else:
            pecan.abort(404)

    @index.when(method='PUT', template='json')
    def put(self, project_id):
        quota = collections.defaultdict(dict)
        quota[project_id] = collections.defaultdict(dict)
        context = restcomm.extract_context_from_environ()

        if not request.body:
            pecan.abort(404)
        payload = eval(request.body)
        payload = payload.get('quota_set')

        try:
            for resource, limit in payload.iteritems():
                result = db_api.quota_update(
                    context,
                    project_id=project_id,
                    resource=resource,
                    limit=limit)
                quota[project_id][result.resource] = result.hard_limit
            return quota
        except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)

    @index.when(method='POST', template='json')
    def post(self, project_id):
        quota = collections.defaultdict(dict)
        quota[project_id] = collections.defaultdict(dict)
        context = restcomm.extract_context_from_environ()

        if not request.body:
            pecan.abort(404)
        payload = eval(request.body)
        payload = payload.get('quota_set')
        try:
            for resource, limit in payload.iteritems():
                result = db_api.quota_create(
                    context,
                    project_id=project_id,
                    resource=resource,
                    limit=limit)
                quota[project_id][result.resource] = result.hard_limit
            return quota
        except exceptions.ProjectQuotaNotFound:
            pecan.abort(404)

    @index.when(method='delete', template='json')
    def delete(self, project_id):
        context = restcomm.extract_context_from_environ()

        try:
            if request.body:
                # Delete the mentioned quota limit for the project
                payload = eval(request.body)
                payload = payload.get('quota_set')
                for resource in payload:
                    db_api.quota_destroy(context, project_id, resource)
            else:
                # Delete all quota limits for the project
                db_api.quota_destroy_all(context, project_id)
        except exceptions.ProjectQuotaNotFound:
                pecan.abort(404)

    @expose(generic=True, template='json')
    def sync(self, project_id):
        context = restcomm.extract_context_from_environ()
        if pecan.request.method != 'POST':
            pecan.abort(405)
        self.client.cast(context, 'quota_sync_for_project',
                         project_id=project_id)
        return 'trigered quota sync for ' + project_id


def list_opts():
    yield None, rpc_api_cap_opt
