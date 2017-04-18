#!/bin/bash
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside gate_hook function in devstack gate.

set -ex

GATE_DEST=$BASE/new

# _setup_kingbird_multinode() - Set up two regions test environment
# in devstack multinode job. Kingbird and RegionOne services will be
# enabled in primary node, RegionTwo servies will be enabled in the subnode.
# Currently only two nodes are supported in the test environment.

function _setup_kingbird_multinode {

    PRIMARY_NODE_IP=$(cat /etc/nodepool/primary_node_private)
    SUBNODE_IP=$(head -n1 /etc/nodepool/sub_nodes_private)

    export OVERRIDE_ENABLED_SERVICES="c-api,c-bak,c-sch,c-vol,cinder,"
    export OVERRIDE_ENABLED_SERVICES+="g-api,g-reg,horizon,key,"
    export OVERRIDE_ENABLED_SERVICES+="n-api,n-cauth,n-cond,n-cpu,n-crt,"
    export OVERRIDE_ENABLED_SERVICES+="n-novnc,n-obj,n-sch,"
    export OVERRIDE_ENABLED_SERVICES+="placement-api,placement-client,"
    export OVERRIDE_ENABLED_SERVICES+="q-agt,q-dhcp,q-l3,q-meta,"
    export OVERRIDE_ENABLED_SERVICES+="q-metering,q-svc,"
    export OVERRIDE_ENABLED_SERVICES+="dstat,peakmem_tracker,rabbit,mysql"

    export DEVSTACK_LOCAL_CONFIG="enable_plugin kingbird https://git.openstack.org/openstack/kingbird"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ENABLE_KINGBIRD=True"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service kb-api"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service kb-engine"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"REGION_NAME=RegionOne"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"HOST_IP=$PRIMARY_NODE_IP"
    export DEVSTACK_LOCAL_CONFIG+=$'\n'"NEUTRON_CREATE_INITIAL_NETWORKS=False"

    export DEVSTACK_SUBNODE_CONFIG="REGION_NAME=RegionTwo"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"HOST_IP=$SUBNODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"KEYSTONE_REGION_NAME=RegionOne"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"KEYSTONE_SERVICE_HOST=$PRIMARY_NODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"KEYSTONE_AUTH_HOST=$PRIMARY_NODE_IP"

    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"NEUTRON_CREATE_INITIAL_NETWORKS=False"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"SERVICE_HOST=$SUBNODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"RABBIT_HOST=$SUBNODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"QPID_HOST=$SUBNODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"DATABASE_HOST=$SUBNODE_IP"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"GLANCE_HOSTPORT=$SUBNODE_IP:9292"
    export DEVSTACK_SUBNODE_CONFIG+=$'\n'"Q_HOST=$SUBNODE_IP"
}

if [ "$DEVSTACK_GATE_TOPOLOGY" == "multinode" ]; then
    _setup_kingbird_multinode
    $GATE_DEST/devstack-gate/devstack-vm-gate.sh
fi
