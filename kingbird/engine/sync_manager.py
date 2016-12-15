# Copyright 2017 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading

from oslo_log import log as logging

from kingbird.common import consts
from kingbird.common import context
from kingbird.common import exceptions
from kingbird.common.i18n import _LE
from kingbird.common.i18n import _LI
from kingbird.common import manager
from kingbird.db.sqlalchemy import api as db_api
from kingbird.drivers.openstack import sdk

LOG = logging.getLogger(__name__)


class SyncManager(manager.Manager):
    """Manages tasks related to resource management"""

    def __init__(self, *args, **kwargs):
        super(SyncManager, self).__init__(service_name="sync_manager",
                                          *args, **kwargs)
        self.context = context.get_admin_context()

    def _create_keypairs_in_region(self, job_id, force, target_regions,
                                   source_keypair, user_id):
        regions_thread = list()
        for region in target_regions:
            thread = threading.Thread(target=self._create_keypairs,
                                      args=(job_id, force, region,
                                            source_keypair, user_id,))
            regions_thread.append(thread)
            thread.start()
            for region_thread in regions_thread:
                region_thread.join()

    def _create_keypairs(self, job_id, force, region, source_keypair, user_id):
        os_client = sdk.OpenStackDriver(region)
        try:
            os_client.create_keypairs(force, source_keypair, user_id)
            LOG.info(_LI('keypair %(keypair)s created in %(region)s')
                     % {'keypair': source_keypair.name, 'region': region})
            try:
                db_api.resource_sync_update(self.context, job_id, region,
                                            source_keypair.name,
                                            consts.SUCCESS)
            except exceptions.JobNotFound():
                raise
        except Exception as exc:
            LOG.error(_LE('Exception Occurred: %(msg)s in %(region)s')
                      % {'msg': exc.message, 'region': region})
            try:
                db_api.resource_sync_update(self.context, job_id, region,
                                            source_keypair.name,
                                            consts.FAILURE)
            except exceptions.JobNotFound():
                raise
            pass

    def keypair_sync_for_user(self, user_id, job_id, payload):
        LOG.info(_LI("Keypair sync Called for user: %s"),
                 user_id)
        keypairs_thread = list()
        target_regions = payload['target']
        force = eval(str(payload.get('force', False)))
        resource_ids = payload.get('resources')
        source_os_client = sdk.OpenStackDriver(payload['source'])
        for keypair in resource_ids:
            source_keypair = source_os_client.get_keypairs(user_id,
                                                           keypair)
            thread = threading.Thread(target=self._create_keypairs_in_region,
                                      args=(job_id, force, target_regions,
                                            source_keypair, user_id,))
            keypairs_thread.append(thread)
            thread.start()
            for keypair_thread in keypairs_thread:
                keypair_thread.join()

        # Update the  parent_db after the sync
        try:
            resource_sync_details = db_api.\
                resource_sync_status(self.context, job_id)
        except exceptions.JobNotFound:
            raise
        result = consts.SUCCESS
        if consts.FAILURE in resource_sync_details:
            result = consts.FAILURE
        try:
            db_api.sync_job_update(self.context, job_id, result)
        except exceptions.JobNotFound:
            raise
