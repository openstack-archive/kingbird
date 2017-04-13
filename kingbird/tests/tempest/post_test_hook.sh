#!/bin/bash -xe

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

export DEST=$BASE/new
export DEVSTACK_DIR=$DEST/devstack
export KINGBIRD_DIR=$DEST/kingbird
export KINGBIRD_DEVSTACK_PLUGIN_DIR=$TRICIRCLE_DIR/devstack
export KINGBIRD_TEMPEST_PLUGIN_DIR=$TRICIRCLE_DIR/kingbird/tests/tempest
export TEMPEST_DIR=$DEST/tempest
export TEMPEST_CONF=$TEMPEST_DIR/etc/tempest.conf

# execute test only in the primary node(i.e, RegionOne)
if [ "$OS_REGION_NAME" -ne "RegionOne" ]; then
    return 0
fi

PRIMARY_NODE_IP=$(cat /etc/nodepool/primary_node_private)

# use admin role to create Tricircle top Pod and Pod1
source $DEVSTACK_DIR/openrc admin admin
unset OS_REGION_NAME

mytoken=$(openstack --os-region-name=RegionOne token issue | awk 'NR==5 {print $4}')
echo $mytoken

image_id=$(openstack --os-region-name=RegionOne image list | awk 'NR==4 {print $2}')

# preparation for the tests
cd $TEMPEST_DIR
if [ -d .testrepository ]; then
  sudo rm -r .testrepository
fi

sudo chown -R jenkins:stack $DEST/tempest

# change the tempest configruation to test Kingbird
env | grep OS_

# import functions needed for the below workaround
source $DEVSTACK_DIR/functions

# designate is a good example how to config TEMPEST_CONF
iniset $TEMPEST_CONF auth admin_username ${ADMIN_USERNAME:-"admin"}
iniset $TEMPEST_CONF auth admin_project_name admin
iniset $TEMPEST_CONF auth admin_password $OS_PASSWORD
iniset $TEMPEST_CONF identity uri $OS_AUTH_URL
iniset $TEMPEST_CONF identity-feature-enabled api_v3 false

iniset $TEMPEST_CONF compute region RegionOne
iniset $TEMPEST_CONF compute image_ref $image_id
iniset $TEMPEST_CONF compute image_ref_alt $image_id

iniset $TEMPEST_CONF volume region RegionOne
iniset $TEMPEST_CONF volume catalog_type volumev2
iniset $TEMPEST_CONF volume endpoint_type publicURL
iniset $TEMPEST_CONF volume-feature-enabled api_v1 false

iniset $TEMPEST_CONF validation connect_method fixed


# Run the Tempest tests through ostestr command
# preparation for the tests

cd $TEMPEST_DIR

# ping kingbird api
curl http://$PRIMARY_NODE_IP:8118

# specify what kingbird test cases to be tested in TESTCASES environment
# variables, then uncomment the follow line
# ostestr --regex $TESTCASES
