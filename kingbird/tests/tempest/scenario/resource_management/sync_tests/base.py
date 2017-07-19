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

import ast
from glanceclient import Client as gl_client
from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client
from kingbirdclient.api.v1 import client as kb_client
from novaclient import client as nv_client
import six
import tempest.test

from tempest.api.compute import base as kp_base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils

from kingbird.tests.tempest.scenario import consts

CONF = config.CONF
KINGBIRD_URL = CONF.kingbird.endpoint_url + CONF.kingbird.api_version
NOVA_API_VERSION = "2.37"
GLANCE_API_VERSION = "2"


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

    def _image_sync_job_create(self, force, **kwargs):
        result = dict()
        images = self._create_images(**kwargs)
        admin_client = self._get_admin_keystone()
        regions = self._get_regions(admin_client)
        target_regions = regions
        target_regions.remove(self.client.region)
        # Now sync the created images in other regions.
        create_response = self._sync_job_create(
            consts.IMAGE_RESOURCE_TYPE, target_regions, images.keys(),
            force=force)
        job_id = create_response.get('job_status').get('id')
        result['job_id'] = job_id
        result['admin'] = admin_client
        result['target'] = target_regions
        result['images'] = images
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


class BaseKBImageTest(tempest.test.BaseTestCase):
    """Base test class for Image API tests."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseKBImageTest, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseKBImageTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseKBImageTest, cls).setup_clients()
        cls.client = cls.os.image_client_v2

    @classmethod
    def resource_setup(cls):
        super(BaseKBImageTest, cls).resource_setup()
        cls.created_images = []

    @classmethod
    def resource_cleanup(cls):
        for image_id in cls.created_images:
            test_utils.call_and_ignore_notfound_exc(
                cls.client.delete_image, image_id)

        for image_id in cls.created_images:
                cls.client.wait_for_resource_deletion(image_id)
        super(BaseKBImageTest, cls).resource_cleanup()

    @classmethod
    def create_and_upload_image(cls, data=None, **kwargs):
        """Wrapper that returns a test image."""
        if 'name' not in kwargs:
            name = data_utils.rand_name("kb-image")
            kwargs['name'] = name

        params = cls._get_create_params(**kwargs)
        if data:
            # NOTE: On glance v1 API, the data should be passed on
            # a header. Then here handles the data separately.
            params['data'] = data

        image = cls.client.create_image(**params)
        # Image objects returned by the v1 client have the image
        # data inside a dict that is keyed against 'image'.
        if 'image' in image:
            image = image['image']
        cls.created_images.append(image['id'])
        # Upload image to glance artifactory.
        file_content = data_utils.random_bytes()
        image_file = six.BytesIO(file_content)
        cls.client.store_image_file(image['id'], image_file)
        cls.kingbird_client = kb_client.Client(
            kingbird_url=KINGBIRD_URL, auth_token=cls.client.token,
            project_id=cls.client.tenant_id)
        return image

    @classmethod
    def _get_create_params(cls, **kwargs):
        return kwargs

    def _get_endpoint_from_region(self, keystone_admin, region):
        services_list = keystone_admin.services.list()
        endpoints_list = keystone_admin.endpoints.list()
        service_id = [service.id for service in
                      services_list if service.type == 'image'][0]

        glance_endpoint = [endpoint.url for endpoint in
                           endpoints_list
                           if endpoint.service_id == service_id
                           and endpoint.region == region and
                           endpoint.interface == 'public'][0]
        return glance_endpoint

    def _create_images(self, **kwargs):
        images = dict()
        for _ in range(2):
            image = self.create_and_upload_image(**kwargs)
            images[image['id']] = image['name']
        return images

    def _sync_ami_image(self, force, ami_id):
        result = dict()
        admin_client = self._get_admin_keystone()
        regions = self._get_regions(admin_client)
        target_regions = regions
        target_regions.remove(self.client.region)
        # Now sync the created images in other regions.
        create_response = self._sync_job_create(
            consts.IMAGE_RESOURCE_TYPE, target_regions, [ami_id],
            force=force)
        job_id = create_response.get('job_status').get('id')
        result['job_id'] = job_id
        result['admin'] = admin_client
        result['target'] = target_regions
        result['images'] = ami_id
        return result

    def _check_image_properties_in_target_region(self, image, **kwargs):
        if 'architecture' in kwargs:
            self.assertEqual(image.architecture,
                             kwargs['architecture'])
        if 'hypervisor_type' in kwargs:
            self.assertEqual(image.hypervisor_type,
                             kwargs['hypervisor_type'])
        if 'ramdisk_id' in kwargs:
            self.assertIsNotNone(image.ramdisk_id)
        if 'kernel_id' in kwargs:
            self.assertIsNotNone(image.kernel_id)

        self.assertEqual(image.container_format,
                         kwargs['container_format'])
        self.assertEqual(image.disk_format,
                         kwargs['disk_format'])
        self.assertEqual(image.visibility,
                         kwargs['visibility'])

    def _check_images_delete_target_region(self, keystone_admin,
                                           target_regions, images,
                                           force, **kwargs):
        for region in target_regions:
            for image in images:
                region_endpoint = self._get_endpoint_from_region(
                    keystone_admin, region)
                glance_client = gl_client(GLANCE_API_VERSION,
                                          session=self.sess,
                                          endpoint=region_endpoint)
                target_region_images = glance_client.images.list()
                for target_image in target_region_images:
                    if target_image['name'] == images[image]:
                        region_image = glance_client.images.\
                            get(target_image['id'])
                        if ast.literal_eval(force):
                            self.assertNotEqual(region_image.id, image)
                        else:
                            self.assertEqual(region_image.id, image)
                        self._check_image_properties_in_target_region(
                            region_image, **kwargs)
                        glance_client.images.delete(target_image['id'])

    def _check_and_delete_dependent_images_target_region(self, keystone_admin,
                                                         target_regions, image,
                                                         force, **kwargs):
        for region in target_regions:
            region_endpoint = self._get_endpoint_from_region(keystone_admin,
                                                             region)
            glance_client = gl_client(GLANCE_API_VERSION, session=self.sess,
                                      endpoint=region_endpoint)
            target_region_images = glance_client.images.list()
            for target_image in target_region_images:
                if target_image['name'] == image['name']:
                    region_image = glance_client.images.\
                        get(target_image['id'])
                    self._check_image_properties_in_target_region(
                        region_image, **kwargs)
                    if ast.literal_eval(force):
                        self.assertNotEqual(region_image.id, image['id'])
                    else:
                        self.assertEqual(region_image.id, image['id'])
                    source_aki_image = glance_client.images.get(
                        region_image.kernel_id)
                    glance_client.images.delete(source_aki_image.id)
                    source_ari_image = glance_client.images.get(
                        region_image.ramdisk_id)
                    glance_client.images.delete(source_ari_image.id)
                    glance_client.images.delete(target_image['id'])
