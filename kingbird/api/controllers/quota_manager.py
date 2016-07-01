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
from oslo_log import versionutils
import pecan
from pecan import expose
from pecan import request

import restcomm
import six

from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.common import utils
from kingbird.db.sqlalchemy import api as db_api
from kingbird.rpc import client as rpc_client

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
        self.rpc_client = rpc_client.EngineClient()

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project_id, action=None):
        quota = collections.defaultdict(dict)
        context = restcomm.extract_context_from_environ()
        result = collections.defaultdict(dict)
        try:
            if project_id == 'defaults':
                # Get default quota limits from conf file
                result = self._get_defaults(context,
                                            CONF.kingbird_global_limit)
            else:
                if action and action != 'detail':
                    pecan.abort(404, _('Invalid request URL'))
                elif action == 'detail':
                    # Get the current quota usages for a project
                    result = self.rpc_client.get_total_usage_for_tenant(
                        context, project_id)
                else:
                    # Get quota limits for all the resources for a project
                    result = db_api.quota_get_all_by_project(
                        context, project_id)
            quota['quota_set'] = result
            return quota
        # Could be raised by get total usage call
        except exceptions.InternalError:
            pecan.abort(400, _('Error while requesting usage'))

    # Tries to update quota limits for a project, if it fails then
    # it creates a new entry in DB for that project
    @index.when(method='PUT', template='json')
    def put(self, project_id, action=None):
        quota = collections.defaultdict(dict)
        quota[project_id] = collections.defaultdict(dict)
        context = restcomm.extract_context_from_environ()
        if action and action != 'sync':
            pecan.abort(404, 'Invalid action, only sync is allowed')
        elif action == 'sync':
            return self.sync(project_id, context)
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))
        if not request.body:
            pecan.abort(400, _('Body required'))
        payload = eval(request.body)
        payload = payload.get('quota_set')
        if not payload:
            pecan.abort(400, _('quota_set in body is required'))
        try:
            utils.validate_quota_limits(payload)
            for resource, limit in payload.iteritems():
                try:
                    # Update quota limit in DB
                    result = db_api.quota_update(
                        context,
                        project_id=project_id,
                        resource=resource,
                        limit=limit)
                except exceptions.ProjectQuotaNotFound:
                    # If update fails due to project/quota not found
                    # then create the quota limit
                    result = db_api.quota_create(
                        context,
                        project_id=project_id,
                        resource=resource,
                        limit=limit)
                quota[project_id][result.resource] = result.hard_limit
            return quota
        except exceptions.InvalidInputError:
            pecan.abort(400, _('Invalid input for quota limits'))

    @index.when(method='delete', template='json')
    def delete(self, project_id):
        context = restcomm.extract_context_from_environ()
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))

        try:
            if request.body:
                # Delete the mentioned quota limit for the project
                payload = eval(request.body)
                payload = payload.get('quota_set')
                if not payload:
                    pecan.abort(400, _('quota_set in body required'))
                utils.validate_quota_limits(payload)
                for resource in payload:
                    db_api.quota_destroy(context, project_id, resource)
                return {'Deleted quota limits': payload}
            else:
                # Delete all quota limits for the project
                db_api.quota_destroy_all(context, project_id)
                return "Deleted all quota limits for the given project"
        except exceptions.ProjectQuotaNotFound:
            pecan.abort(404, _('Project quota not found'))
        except exceptions.InvalidInputError:
            pecan.abort(400, _('Invalid input for quota'))

    # Private method called by put method for on demand quota sync
    def sync(self, project_id, context):
        if pecan.request.method != 'PUT':
            pecan.abort(405, _('Bad method. Use PUT instead'))
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))

        self.rpc_client.quota_sync_for_project(
            context, project_id)
        return 'triggered quota sync for ' + project_id

    @staticmethod
    def _get_defaults(context, config_defaults):
        """Get default quota values.

        If the default class is defined, use the values defined
        in the class, otherwise use the values from the config.

        :param context:
        :param config_defaults:
        :return:
        """
        quotas = {}
        default_quotas = {}
        if CONF.use_default_quota_class:
            default_quotas = db_api.quota_class_get_default(context)

        for resource, default in six.iteritems(config_defaults):
            # get rid of the 'quota_' prefix
            resource_name = resource[6:]
            if default_quotas:
                if resource_name not in default_quotas:
                    versionutils.report_deprecated_feature(LOG, _(
                        "Default quota for resource: %(res)s is set "
                        "by the default quota flag: quota_%(res)s, "
                        "it is now deprecated. Please use the "
                        "default quota class for default "
                        "quota.") % {'res': resource_name})
            quotas[resource_name] = default_quotas.get(resource_name, default)

        return quotas
