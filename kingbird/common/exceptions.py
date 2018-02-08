# Copyright 2015 Huawei Technologies Co., Ltd.
# Copyright 2015 Ericsson AB.
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
Kingbird base exception handling.
"""
import six

from oslo_utils import excutils

from kingbird.common.i18n import _


class KingbirdException(Exception):
    """Base Kingbird Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """

    message = _("An unknown exception occurred.")

    def __init__(self, **kwargs):
        try:
            super(KingbirdException, self).__init__(self.message % kwargs)
            self.msg = self.message % kwargs
        except Exception:
            with excutils.save_and_reraise_exception() as ctxt:
                if not self.use_fatal_exceptions():
                    ctxt.reraise = False
                    # at least get the core message out if something happened
                    super(KingbirdException, self).__init__(self.message)

    if six.PY2:
        def __unicode__(self):
            return unicode(self.msg)

    def use_fatal_exceptions(self):
        return False


class BadRequest(KingbirdException):
    message = _('Bad %(resource)s request: %(msg)s')


class NotFound(KingbirdException):
    pass


class Conflict(KingbirdException):
    pass


class NotAuthorized(KingbirdException):
    message = _("Not authorized.")


class ServiceUnavailable(KingbirdException):
    message = _("The service is unavailable")


class AdminRequired(NotAuthorized):
    message = _("User does not have admin privileges: %(reason)s")


class InUse(KingbirdException):
    message = _("The resource is inuse")


class InvalidConfigurationOption(KingbirdException):
    message = _("An invalid value was provided for %(opt_name)s: "
                "%(opt_value)s")


class ProjectQuotaNotFound(NotFound):
    message = _("Quota for project %(project_id) doesn't exist.")


class QuotaClassNotFound(NotFound):
    message = _("Quota class %(class_name) doesn't exist.")


class JobNotFound(NotFound):
    message = _("Job doesn't exist.")


class DependentImageNotFound(NotFound):
    message = _("Dependent image doesn't exist.")


class ImageFormatNotSupported(KingbirdException):
    message = _("An invalid version was provided")


class ConnectionRefused(KingbirdException):
    message = _("Connection to the service endpoint is refused")


class TimeOut(KingbirdException):
    message = _("Timeout when connecting to OpenStack Service")


class InternalError(KingbirdException):
    message = _("Error when performing operation")


class InvalidInputError(KingbirdException):
    message = _("An invalid value was provided")


class ResourceNotFound(NotFound):
    message = _("Resource not available")
