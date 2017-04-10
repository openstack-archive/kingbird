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
from oslo_utils import uuidutils
import pecan
from pecan import expose
from pecan import request

from kingbird.api.controllers import restcomm
from kingbird.api import enforcer as enf
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


class BaseController(object):
    """Base controller of quota_management for API version 1.0 & 1.1.

    It references all other resources belonging to both the API's.
    """

    def __init__(self, *args, **kwargs):
        super(BaseController, self).__init__(*args, **kwargs)
        self.rpc_client = rpc_client.EngineClient()

    def get_quota(self, context, project_id, action=None):
        """Get quota for a specified tenant.

        :param context: context object.

        :param project_id: It's UUID of the project.
            Note: In v1.0 it can be defaults sometimes.
            Only specified tenant quota is retrieved from database
            using this param.

        :param action: Optional. If provided, it can be 'detail'
            action - Gets details quota for the specified tenant.
        """
        result = collections.defaultdict(dict)
        if project_id == 'defaults' or action == 'defaults':
            # Get default quota limits from conf file
            result = self.get_defaults(context,
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
                result = db_api.quota_get_all_by_project(context, project_id)
        return result

    def get_defaults(self, context, config_defaults):
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

        for resource, default in config_defaults.items():
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

    def sync(self, context, project_id):
        """Sync quota of a tenant.

        Private method called by put method for on demand quota sync

        :param context: context object.

        :param project_id: It's UUID of the project.
            On demand quota sync is triggered only for specified tenant
            using this param.
        """
        if pecan.request.method != 'PUT':
            pecan.abort(405, _('Bad method. Use PUT instead'))

        self.rpc_client.quota_sync_for_project(
            context, project_id)
        return 'triggered quota sync for ' + project_id

    def delete_quota_resources(self, context, project_id, payload):
        """Delete quota for a specified resource of a tenant.

        :param context: context object.

        :param project_id: It's UUID of the project.
            Only specified tenant quota is retrieved from database
            using this param.

        :param payload: Deletes quota of specified resources for a tenant.
            Note:- Support only through CURL request for V1.0.
        """
        try:
            # Delete the mentioned quota limit for the project
            utils.validate_quota_limits(payload)
            for resource in payload:
                db_api.quota_destroy(context, project_id, resource)
            return {'Deleted quota limits': payload}
        except exceptions.ProjectQuotaNotFound:
            pecan.abort(404, _('Project quota not found'))
        except exceptions.InvalidInputError:
            pecan.abort(400, _('Invalid input for quota'))

    def delete_quota(self, context, project_id):
        """Delete entire quota for a specified tenant.

        :param context: context object.

        :param project_id: It's UUID of the project.
            Only specified tenant quota is retrieved from database
            using this param.
        """
        try:
            db_api.quota_destroy_all(context, project_id)
            return "Deleted all quota limits for the given project"
        except exceptions.ProjectQuotaNotFound:
            pecan.abort(404, _('Project quota not found'))

    def update_quota(self, context, request, project_id):
        """Update quota for specified tenant.

        :param context: context object.

        :param request: request object.

        :param project_id: It's UUID of the project.
            Only specified tenant quota is updated in database
            using this param.
        """
        quota = collections.defaultdict(dict)
        quota[project_id] = collections.defaultdict(dict)
        if not request.body:
            pecan.abort(400, _('Body required'))
        payload = eval(request.body).get('quota_set')
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


class QuotaManagerController(BaseController):
    """Quota Management API controller for API version 1.0.

    It references all other resources belonging to the API v1.0.
    """

    VERSION_ALIASES = {
        'mitaka': '1.0',
    }

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.0
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project_id, target_project_id=None, action=None):
        """Get quota for a specified tenant.

        :param project_id: It's UUID of the project.

        :param target_project_id: It's UUID of the project.
            Note: In v1.0 it can be defaults sometimes.
            Only specified tenant quota is retrieved from database
            using this param.

        :param action: Optional. If provided, it can be 'detail'
            detail - Gets detail quota usage for the specified tenant.
        """
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        if not uuidutils.is_uuid_like(target_project_id)\
                and target_project_id != 'defaults':
            pecan.abort(400, _('Invalid request URL'))
        quota = collections.defaultdict(dict)
        try:
            if context.is_admin or (project_id == target_project_id)\
                    or (target_project_id == 'defaults'):
                result = self.get_quota(context, target_project_id, action)
                quota['quota_set'] = result
                return quota
            else:
                pecan.abort(403, _('Admin required '))
        except exceptions.InternalError:
            pecan.abort(400, _('Error while requesting usage'))

    @index.when(method='PUT', template='json')
    def put(self, project_id, target_project_id, action=None):
        """Update quota limits for a project.

        If it fails, Then creates a new entry in DB for that project.

        :param project_id: It's UUID of the project.

        :param target_project_id: It's UUID of the project.
            Note: In v1.0 it can be defaults sometimes.
            Only specified tenant quota is retrieved from database
            using this param.

        :param action: Optional. If provided, it can be 'detail'
            detail - Gets detail quota usage for the specified tenant.
        """
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        if not uuidutils.is_uuid_like(target_project_id):
            pecan.abort(400, _('Invalid request URL'))
        if action and action != 'sync':
            pecan.abort(404, 'Invalid action, only sync is allowed')
        elif action == 'sync':
            return self.sync(context, target_project_id)
        quota = self.update_quota(context, request, target_project_id)
        return quota

    @index.when(method='delete', template='json')
    def delete(self, project_id, target_project_id):
        """Delete quota for a specified tenant.

        Resources for a specific tenant can also be deleted.

        :param project_id: It's UUID of the project.

        :param target_project_id: It's UUID of the project.
            Note: In v1.0 it can be defaults sometimes.
            Only specified tenant quota is retrieved from database
            using this param.

        #NOTE: Support to delete quota for a specific resource is through CURL
               request in V1.0.
        """
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        if not uuidutils.is_uuid_like(target_project_id):
            pecan.abort(400, _('Invalid request URL'))
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))
        if request.body:
            payload = eval(request.body).get('quota_set')
            if not payload:
                pecan.abort(400, _('quota_set in body required'))
            self.delete_quota_resources(context, target_project_id, payload)
            return {'Deleted quota limits': payload}
        else:
            self.delete_quota(context, target_project_id)
            return "Deleted all quota limits for the given project"


class QuotaManagerV1Controller(BaseController):
    """Quota Management API controller for API version 1.1.

    It references all other resources belonging to the API v1.1.
    """

    VERSION_ALIASES = {
        'PIKE': '1.1',
    }

    # to do the version compatibility for future purpose
    def _determine_version_cap(self, target):
        version_cap = 1.1
        return version_cap

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project_id, action=None):
        """Get quota of a tenant.

        :param project_id: It's UUID of the project.
            Only specified quota details can be viewed using this param.

        :param action: Optional. If provided, it can be 'defaults' or 'detail'
            defaults - returns the quotas limits from the conf file.
            detail - returns the current quota usages of the tenant
        """
        context = restcomm.extract_context_from_environ()
        quota = collections.defaultdict(dict)
        result = collections.defaultdict(dict)
        if not uuidutils.is_uuid_like(project_id):
            pecan.abort(400)
        enforce = enf.enforce('kingbird:get_all_quota', context)
        try:
            if enforce or (project_id == context.project)\
                    or (action == 'defaults'):
                result = self.get_quota(context, project_id, action)
                quota['quota_set'] = result
                return quota
            else:
                pecan.abort(403, _('Admin required '))
        except exceptions.InternalError:
            pecan.abort(400, _('Error while requesting usage'))

    @index.when(method='PUT', template='json')
    def put(self, project_id, action=None):
        """Update quota of a tenant.

        :param project_id: It's UUID of the project.
            Only specified tenant quota is updated using this param.

        :param action: Optional. If provided, it can be 'sync'
            action - syncs quota for the specified tenant
            based on the kingbird magic.
        """
        context = restcomm.extract_context_from_environ()
        quota = collections.defaultdict(dict)
        quota[project_id] = collections.defaultdict(dict)
        if not uuidutils.is_uuid_like(project_id):
            pecan.abort(400)
        enforce = enf.enforce('kingbird:update_quota', context)
        if not enforce:
            pecan.abort(403, _('Admin required'))
        if action not in ('sync', None):
            pecan.abort(404, 'Invalid action, only sync is allowed')
        elif action == 'sync':
            return self.sync(context, project_id)
        quota = self.update_quota(context, request, project_id)
        return quota

    @index.when(method='delete', template='json')
    def delete(self, project_id, **args):
        """Delete quota of a tenant.

        :param project_id: It's UUID of the project.
            Only specified tenant quota is deleted using this param.
        """
        context = restcomm.extract_context_from_environ()
        if not uuidutils.is_uuid_like(project_id):
            pecan.abort(400)
        enforce = enf.enforce('kingbird:delete_quota', context)
        if not enforce:
            pecan.abort(403, _('Admin required'))
        if args:
            payload = args.keys()
            if not payload:
                pecan.abort(400, _('quota_set in body required'))
            self.delete_quota_resources(context, project_id, payload)
            return {'Deleted quota limits': payload}
        else:
            # Delete all quota limits for the project
            self.delete_quota(context, project_id)
            return "Deleted all quota limits for the given project"
