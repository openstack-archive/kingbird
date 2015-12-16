# Copyright 2015 Huawei Technologies Co., Ltd.
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

from oslo_context import context as oslo_ctx


class ContextBase(oslo_ctx.RequestContext):
    def __init__(self, auth_token=None, user_id=None, tenant_id=None,
                 is_admin=False, request_id=None, overwrite=True,
                 user_name=None, tenant_name=None, auth_url=None,
                 region=None, password=None, domain='default', **kwargs):
        super(ContextBase, self).__init__(
            auth_token=auth_token,
            user=user_id or kwargs.get('user', None),
            tenant=tenant_id or kwargs.get('tenant', None),
            domain=kwargs.get('domain', None),
            user_domain=kwargs.get('user_domain', None),
            project_domain=kwargs.get('project_domain', None),
            is_admin=is_admin,
            read_only=kwargs.get('read_only', False),
            show_deleted=kwargs.get('show_deleted', False),
            request_id=request_id,
            resource_uuid=kwargs.get('resource_uuid', None),
            overwrite=overwrite)
        self.user_name = user_name
        self.tenant_name = tenant_name
        self.auth_url = auth_url
        self.password = password
        self.default_name = domain
        self.region_name = region

    def to_dict(self):
        ctx_dict = super(ContextBase, self).to_dict()
        ctx_dict.update({
            'user_name': self.user_name,
            'tenant_name': self.tenant_name,
            'auth_url': self.auth_url,
            'password': self.password,
            'default_name': self.default_name,
            'region_name': self.region_name,
        })
        return ctx_dict

    @classmethod
    def from_dict(cls, ctx):
        return cls(**ctx)


class Context(ContextBase):
    def __init__(self, **kwargs):
        super(Context, self).__init__(**kwargs)
        self._session = None

    @property
    def session(self):
        # todo get db session in the context
        # if not self._session:
            # self._session = dal.get_session()
        return self._session


def get_admin_context(read_only=True):
    return ContextBase(user_id=None,
                       project_id=None,
                       is_admin=True,
                       overwrite=False,
                       read_only=read_only)
