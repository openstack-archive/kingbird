# Copyright 2017 Ericsson AB.
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

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client
from kingbirdclient.api.v1 import client as kb_client

from tempest.api.compute import base as kp_base
from tempest import config
from tempest.lib.common.utils import data_utils

from kingbird.tests.tempest.scenario import consts
from novaclient import client as nv_client

CONF = config.CONF
KINGBIRD_URL = CONF.kingbird.endpoint_url + CONF.kingbird.api_version
NOVA_API_VERSION = "2.37"


class BaseKingbirdClass(object):

    def _keypair_sync_job_create(self, force, keys=None):
        result = dict()
        admin_client = self._get_admin_keystone()
        regions = self._get_regions(admin_client)
        target_regions = regions
        target_regions.remove(self.client.region)
        if keys:
            create_response = self._sync_job_create(
                consts.KEYPAIR_RESOURCE_TYPE, target_regions, keys,
                force=force)
            result['keys'] = keys
        else:
            key_list = self._create_keypairs()
            # Now sync all the keypairs in other regions.
            create_response = self._sync_job_create(
                consts.KEYPAIR_RESOURCE_TYPE, target_regions, key_list,
                force=force)
            result['keys'] = key_list
        job_id = create_response.get('job_status').get('id')
        result['job_id'] = job_id
        result['admin'] = admin_client
        result['target'] = target_regions
        return result

    def _check_job_status(self):
        # Wait until the status of the job is not "IN_PROGRESS"
        job_list_resp = self.get_sync_job_list()
        status = job_list_resp.get('job_set')[0].get('sync_status')
        return status != consts.JOB_PROGRESS

    def _sync_job_create(self, resource_type, target_regions, resource_list,
                         force):
        # JSON body used to sync resource.
        body = {"resource_type": resource_type,
                "resources": resource_list,
                "source": self.client.region, "force": force,
                "target": target_regions}
        response = self.sync_resource(body)
        return response

    def _get_admin_keystone(self):
        auth = v3.Password(
            auth_url=CONF.identity.uri_v3,
            username=CONF.auth.admin_username,
            password=CONF.auth.admin_password,
            project_name=CONF.auth.admin_project_name,
            user_domain_name=CONF.auth.admin_domain_name,
            project_domain_name=CONF.auth.admin_domain_name)
        self.sess = session.Session(auth=auth)
        keystone_admin = ks_client.Client(session=self.sess)
        return keystone_admin

    def _get_regions(self, keystone_admin):
        regions = [current_region.id for current_region in
                   keystone_admin.regions.list()]
        return regions

    def sync_resource(self, post_body):
        response = self.kingbird_client.sync_manager.\
            sync_resources(**post_body)
        result = dict()
        for i in response:
            result['id'] = i.id
            result['status'] = i.status
            result['created_at'] = i.created_at
        res = dict()
        res['job_status'] = result
        return res

    def delete_db_entries(self, job_id):
        self.kingbird_client.sync_manager.delete_sync_job(job_id)

    def get_sync_job_list(self, action=None):
        response = self.kingbird_client.sync_manager.list_sync_jobs(action)
        result = dict()
        job_set = list()
        res = dict()
        for i in response:
            result['id'] = i.id
            result['sync_status'] = i.status
            result['created_at'] = i.created_at
            result['updated_at'] = i.updated_at
            job_set.append(result.copy())
        res['job_set'] = job_set
        return res

    def get_sync_job_detail(self, job_id):
        response = self.kingbird_client.sync_manager.sync_job_detail(job_id)
        result = dict()
        job_set = list()
        res = dict()
        for i in response:
            result['resource'] = i.resource_name
            result['target_region'] = i.target_region
            result['sync_status'] = i.status
            result['created_at'] = i.created_at
            result['updated_at'] = i.updated_at
            result['source_region'] = i.source_region
            result['resource_type'] = i.resource_type
            job_set.append(result.copy())
        res['job_set'] = job_set
        return res


class BaseKBKeypairTest(kp_base.BaseV2ComputeTest):
    """Base test case class for all keypair API tests."""

    @classmethod
    def setup_clients(cls):
        super(BaseKBKeypairTest, cls).setup_clients()
        cls.client = cls.keypairs_client

    def _create_keypairs(self):
        key_list = list()
        for _ in range(2):
            keypair = self.create_keypair()
            key_list.append(keypair['name'])
        return key_list

    def _check_keypairs_in_target_region(self, target_regions, key_list):
        for region in target_regions:
            for keypair in key_list:
                nova_client = nv_client.Client(NOVA_API_VERSION,
                                               session=self.sess,
                                               region_name=region)
                source_keypair = nova_client.keypairs.get(
                    keypair, self.client.user_id)
                self.assertEqual(source_keypair.name, keypair)

    def _cleanup_resources(self, key_list, regions, user_id):
        for region in regions:
            for key in key_list:
                nova_client = nv_client.Client(NOVA_API_VERSION,
                                               session=self.sess,
                                               region_name=region)
                nova_client.keypairs.delete(key, user_id)

    def _delete_keypair(self, keypair_name, **params):
        self.client.delete_keypair(keypair_name, **params)

    def create_keypair(self, keypair_name=None,
                       pub_key=None, keypair_type=None,
                       user_id=None):
        if keypair_name is None:
            keypair_name = data_utils.rand_name('kb-keypair')
        kwargs = {'name': keypair_name}
        delete_params = {}
        if pub_key:
            kwargs.update({'public_key': pub_key})
        if keypair_type:
            kwargs.update({'type': keypair_type})
        if user_id:
            kwargs.update({'user_id': user_id})
            delete_params['user_id'] = user_id
        body = self.client.create_keypair(**kwargs)['keypair']
        self.kingbird_client = kb_client.Client(
            kingbird_url=KINGBIRD_URL, auth_token=self.client.token,
            project_id=self.client.tenant_id)
        self.addCleanup(self._delete_keypair, keypair_name, **delete_params)
        return body
