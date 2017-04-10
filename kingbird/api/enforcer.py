# Copyright 2017 Ericsson AB.
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

"""Policy enforcer for Kingbird."""

from oslo_config import cfg
from oslo_policy import policy

from kingbird.common import exceptions as exc


_ENFORCER = None


def enforce(action, context, target=None, do_raise=True,
            exc=exc.NotAuthorized):
    """Verify that the action is valid on the target in this context.

    :param action: String, representing the action to be checked.
                   This should be colon separated for clarity.
                   i.e. ``sync:list``
    :param context: Kingbird context.
    :param target: Dictionary, representing the object of the action.
                   For object creation, this should be a dictionary
                   representing the location of the object.
                   e.g. ``{'project_id': context.project}``
    :param do_raise: if True (the default), raises specified exception.
    :param exc: Exception to be raised if not authorized. Default is
                kingbird.common.exceptions.NotAuthorized.

    :return: returns True if authorized and False if not authorized and
             do_raise is False.
    """
    if cfg.CONF.auth_strategy != 'keystone':
        # Policy enforcement is supported now only with Keystone
        # authentication.
        return

    target_obj = {
        'project_id': context.project,
        'user_id': context.user,
    }

    target_obj.update(target or {})
    _ensure_enforcer_initialization()

    try:
        _ENFORCER.enforce(action, target_obj, context.to_dict(),
                          do_raise=do_raise, exc=exc)
        return True

    except Exception:
        return False


def _ensure_enforcer_initialization():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(cfg.CONF)
        _ENFORCER.load_rules()
