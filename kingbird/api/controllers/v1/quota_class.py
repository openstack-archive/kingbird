# Copyright (c) 2016 Ericsson AB
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from oslo_log import log as logging
from oslo_utils import uuidutils
import pecan
from pecan import expose
from pecan import request

from kingbird.api.controllers import restcomm
from kingbird.common import consts
from kingbird.common import exceptions
from kingbird.common.i18n import _
from kingbird.common import utils
from kingbird.db import api as db_api

LOG = logging.getLogger(__name__)


class QuotaClassSetController(object):
    supported_quotas = []

    def __init__(self, *args, **kwargs):
        self.supported_quotas = list(
            consts.CINDER_QUOTA_FIELDS +
            consts.NEUTRON_QUOTA_FIELDS +
            consts.NOVA_QUOTA_FIELDS)

    def _format_quota_set(self, context, quota_class, quota_set):
        """Convert the quota object to a result dict."""
        result = db_api.quota_class_get_default(context)
        if quota_class:
            result['class_name'] = str(quota_class)
        else:
            result = {}

        for quota in self.supported_quotas:
            if quota in quota_set:
                result[quota] = quota_set[quota]

        return dict(quota_class_set=result)

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, project_id, class_name):
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        LOG.info("Fetch quotas for [class_name=%s]" % class_name)

        values = db_api.quota_class_get_all_by_name(context, class_name)

        return self._format_quota_set(context, class_name, values)

    @index.when(method='PUT', template='json')
    def put(self, project_id, class_name):
        """Update a class."""
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        LOG.info("Update quota class [class_name=%s]" % class_name)

        if not context.is_admin:
            pecan.abort(403, _('Admin required'))
        if not request.body:
            pecan.abort(400, _('Body required'))

        quota_class_set = eval(request.body).get('quota_class_set')

        if not quota_class_set:
            pecan.abort(400, _('Missing quota_class_set in the body'))

        utils.validate_quota_limits(quota_class_set)

        for key, value in quota_class_set.items():
            try:
                db_api.quota_class_update(context, class_name, key, value)
            except exceptions.QuotaClassNotFound:
                db_api.quota_class_create(context, class_name, key, value)

        values = db_api.quota_class_get_all_by_name(context, class_name)

        return self._format_quota_set(context, class_name, values)

    @index.when(method='delete', template='json')
    def delete(self, project_id, class_name):
        context = restcomm.extract_context_from_environ()
        valid_project_id = uuidutils.is_uuid_like(project_id)
        if not valid_project_id:
            pecan.abort(400, _('Invalid request URL'))
        if project_id != context.project and not context.is_admin:
            pecan.abort(400, _('Invalid request URL'))
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))

        LOG.info("Delete quota class [class_name=%s]" % class_name)
        try:
            db_api.quota_class_destroy_all(context, class_name)
        except exceptions.QuotaClassNotFound:
            pecan.abort(404, _('Quota class not found'))
