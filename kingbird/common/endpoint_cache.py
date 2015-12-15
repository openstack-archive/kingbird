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

import collections

from keystoneclient.auth.identity import v3 as auth_identity
from keystoneclient.auth import token_endpoint
from keystoneclient import session
from keystoneclient.v3 import client as keystone_client
from oslo_config import cfg

cache_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v3',
               help='keystone authorization url'),
    cfg.StrOpt('identity_url',
               default='http://127.0.0.1:35357/v3',
               help='keystone service url'),
    cfg.StrOpt('admin_username',
               help='username of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_password',
               help='password of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant',
               help='tenant name of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_user_domain_name',
               default='Default',
               help='user domain name of admin account, needed when'
                    ' auto_refresh_endpoint set to True'),
    cfg.StrOpt('admin_tenant_domain_name',
               default='Default',
               help='tenant domain name of admin account, needed when'
                    ' auto_refresh_endpoint set to True')
]
cache_opt_group = cfg.OptGroup('cache')
cfg.CONF.register_group(cache_opt_group)
cfg.CONF.register_opts(cache_opts, group=cache_opt_group)


class EndpointCache(object):
    def __init__(self):
        self.endpoint_map = collections.defaultdict(dict)
        self._update_endpoints()

    @staticmethod
    def _get_admin_token():
        auth = auth_identity.Password(
            auth_url=cfg.CONF.cache.identity_url,
            username=cfg.CONF.cache.admin_username,
            password=cfg.CONF.cache.admin_password,
            project_name=cfg.CONF.cache.admin_tenant,
            user_domain_name=cfg.CONF.cache.admin_user_domain_name,
            project_domain_name=cfg.CONF.cache.admin_tenant_domain_name)
        sess = session.Session(auth=auth)
        return sess.get_token()

    @staticmethod
    def _get_endpoint_from_keystone():
        auth = token_endpoint.Token(cfg.CONF.cache.identity_url,
                                    EndpointCache._get_admin_token())
        sess = session.Session(auth=auth)
        cli = keystone_client.Client(session=sess)

        service_id_name_map = {}
        for service in cli.services.list():
            service_dict = service.to_dict()
            service_id_name_map[service_dict['id']] = service_dict['name']

        region_service_endpoint_map = {}
        for endpoint in cli.endpoints.list():
            endpoint_dict = endpoint.to_dict()
            if endpoint_dict['interface'] != 'public':
                continue
            region_id = endpoint_dict['region']
            service_id = endpoint_dict['service_id']
            url = endpoint_dict['url']
            service_name = service_id_name_map[service_id]
            if region_id not in region_service_endpoint_map:
                region_service_endpoint_map[region_id] = {}
            region_service_endpoint_map[region_id][service_name] = url
        return region_service_endpoint_map

    def _get_endpoint(self, region, service, retry):
        if service not in self.endpoint_map[region]:
            if retry:
                self.update_endpoints()
                return self._get_endpoint(region, service, False)
            else:
                return ''
        else:
            return self.endpoint_map[region][service]

    def _update_endpoints(self):
        endpoint_map = EndpointCache._get_endpoint_from_keystone()

        for region in endpoint_map:
            for service in endpoint_map[region]:
                self.endpoint_map[region][
                    service] = endpoint_map[region][service]

    def get_endpoint(self, region, service):
        """Get service endpoint url

        :param region: region the service belongs to
        :param service: service type
        :return: url of the service
        """
        return self._get_endpoint(region, service, True)

    def update_endpoints(self):
        """Update endpoint cache from Keystone

        :return: None
        """
        self._update_endpoints()

    def get_all_regions(self):
        """Get region list

        return: List of regions
        """
        return self.endpoint_map.keys()
