#!/bin/bash

set -o xtrace
set -o nounset
set -o pipefail

# Ensure that openrc containing OpenStack environment variables is present.
source openrc

# Endpoints. Dynamically get IP addresses from another service (keystone)
KINGBIRD_PUBLIC_URL=$(openstack endpoint list --long | grep keystone | cut -d '|' -f 6 | cut -d '/' -f 3 | cut -d ':' -f 1)
KINGBIRD_ADMIN_URL=$(openstack endpoint list --long | grep keystone | cut -d '|' -f 7 | cut -d '/' -f 3 | cut -d ':' -f 1)
KINGBIRD_INTERNAL_URL=$(openstack endpoint list --long | grep keystone | cut -d '|' -f 7 | cut -d '/' -f 3 | cut -d ':' -f 1)
KINGBIRD_PORT=8118
KINGBIRD_VERSION='v1.0'
# MySQL
mysql_host=$(mysql -uroot -se "SELECT SUBSTRING_INDEX(USER(), '@', -1);")
mysql_user='kingbird'
mysql_pass='mysql_kb'
mysql_db='kingbird'

# Keystone
admin_password='keystone_kb_pass'
admin_user='kingbird'
admin_tenant_name='services'
auth_uri=$OS_AUTH_URL"v3"

# Rabbit
rabbit_user='nova'
rabbit_password=$(sed -n 's/^rabbit_password *= *\([^ ]*.*\)/\1/p' < /etc/nova/nova.conf)
rabbit_hosts=$(sed -n 's/^rabbit_hosts *= *\([^ ]*.*\)/\1/p' < /etc/nova/nova.conf)

# Config
KINGBIRD_CONF_FILE='/etc/kingbird/kingbird.conf'
bind_host=$(sed -n 's/^admin_bind_host *= *\([^ ]*.*\)/\1/p' < /etc/keystone/keystone.conf)

function ini_has_option {
    local file=$1
    local section=$2
    local option=$3
    local line
    line=$(sed -ne "/^\[$section\]/,/^\[.*\]/ { /^$option[ \t]*=/ p; }" "$file")
    [ -n "$line" ]
}

function iniset {
    local file=$1
    local section=$2
    local option=$3
    local value=$4

    [[ -z $section || -z $option ]] && return

    if ! grep -q "^\[$section\]" "$file" 2>/dev/null; then
        echo -e "\n[$section]" >>"$file"
    fi
    if ! ini_has_option "$file" "$section" "$option"; then
        sed -i -e "/^\[$section\]/ a\\
$option = $value
" "$file"
    else
        local sep=$(echo -ne "\x01")
        # Replace it
        sed -i -e '/^\['${section}'\]/,/^\[.*\]/ s'${sep}'^\('${option}'[ \t]*=[ \t]*\).*$'${sep}'\1'"${value}"${sep} "$file"
    fi
}

export DEBIAN_FRONTEND=noninteractive
apt-get -qq update
apt-get install -y  \
        curl \
        git \
        libffi-dev \
        libssl-dev \
        libxml2-dev \
        libxslt1-dev \
        libyaml-dev \
        python-dev \
        python-pip \
        python-setuptools

sudo pip install --upgrade pip
sudo pip install tox==1.6.1


#Recreate database
mysql -uroot -e "DROP DATABASE IF EXISTS $mysql_db;"
mysql -uroot -e "CREATE DATABASE $mysql_db CHARACTER SET utf8;"
mysql -uroot -e "GRANT ALL PRIVILEGES ON $mysql_db.* TO '$mysql_user'@'$mysql_host' IDENTIFIED BY '$mysql_pass';"

#Configure kingbird user
openstack user show kingbird 2>/dev/null
if [ $? -eq 0 ]; then
    echo "User already exists. Skipping.."
else
    echo "Creating Kingbird user.."
    openstack user create --project=${admin_tenant_name} --password=${admin_password} ${admin_user}
    openstack role add --user=${admin_user} --project=${admin_tenant_name} admin
fi

#Configure kingbird endpoints
openstack service show kingbird 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Kingbird service already exists. Skipping.."
else
    echo "Creating Kingbird endpoints.."
    openstack service create --name=kingbird --description="Kingbird" multisite
    openstack endpoint create kingbird \
        --publicurl http://${KINGBIRD_PUBLIC_URL}:${KINGBIRD_PORT}/${KINGBIRD_VERSION} \
        --adminurl http://${KINGBIRD_ADMIN_URL}:${KINGBIRD_PORT}/${KINGBIRD_VERSION} \
        --internalurl http://${KINGBIRD_INTERNAL_URL}:${KINGBIRD_PORT}/${KINGBIRD_VERSION} \
        --region ${OS_REGION_NAME}
fi

#Setup Kingbird
git clone https://github.com/openstack/kingbird.git && cd kingbird/

pip install -r requirements.txt
pip install .

mkdir -p /etc/kingbird/
oslo-config-generator --config-file tools/config-generator.conf --output-file ${KINGBIRD_CONF_FILE}

# Delete previous repo clone
cd ..
rm -rf kingbird/

# Configure host section
iniset ${KINGBIRD_CONF_FILE} DEFAULT bind_host ${bind_host}
iniset ${KINGBIRD_CONF_FILE} DEFAULT bind_port ${KINGBIRD_PORT}
iniset ${KINGBIRD_CONF_FILE} host_details host ${bind_host}

# Configure cache section. Ideally should be removed
iniset ${KINGBIRD_CONF_FILE} cache admin_tenant ${admin_tenant_name}
iniset ${KINGBIRD_CONF_FILE} cache admin_username ${admin_user}
iniset ${KINGBIRD_CONF_FILE} cache admin_password ${admin_password}
iniset ${KINGBIRD_CONF_FILE} cache auth_uri ${auth_uri}
iniset ${KINGBIRD_CONF_FILE} cache identity_uri ${OS_AUTH_URL}

# Configure keystone_authtoken section
iniset ${KINGBIRD_CONF_FILE} keystone_authtoken admin_tenant_name ${admin_tenant_name}
iniset ${KINGBIRD_CONF_FILE} keystone_authtoken admin_user ${admin_user}
iniset ${KINGBIRD_CONF_FILE} keystone_authtoken admin_password ${admin_password}
iniset ${KINGBIRD_CONF_FILE} keystone_authtoken auth_uri ${auth_uri}
iniset ${KINGBIRD_CONF_FILE} keystone_authtoken identity_uri ${OS_AUTH_URL}

# Configure RabbitMQ credentials
iniset ${KINGBIRD_CONF_FILE} oslo_messaging_rabbit rabbit_userid ${rabbit_user}
iniset ${KINGBIRD_CONF_FILE} oslo_messaging_rabbit rabbit_password ${rabbit_password}
iniset ${KINGBIRD_CONF_FILE} oslo_messaging_rabbit rabbit_hosts ${rabbit_hosts}
iniset ${KINGBIRD_CONF_FILE} oslo_messaging_rabbit rabbit_virtual_host /
iniset ${KINGBIRD_CONF_FILE} oslo_messaging_rabbit rabbit_ha_queues False


# Configure the database.
iniset ${KINGBIRD_CONF_FILE} database connection "mysql://$mysql_user:$mysql_pass@$mysql_host/$mysql_db?charset=utf8"
iniset ${KINGBIRD_CONF_FILE} database max_overflow -1
iniset ${KINGBIRD_CONF_FILE} database max_pool_size 1000

# Kill kingbird
if pgrep kingbird-api &> /dev/null ; then  pkill -f kingbird-api ; fi
if pgrep kingbird-engine &> /dev/null ; then  pkill -f kingbird-engine ; fi

# Run kingbird
mkdir -p /var/log/kingbird
kingbird-manage --config-file ${KINGBIRD_CONF_FILE} db_sync
nohup kingbird-engine --config-file ${KINGBIRD_CONF_FILE} --log-file /var/log/kingbird/kingbird-engine.log &
nohup kingbird-api --config-file ${KINGBIRD_CONF_FILE} --log-file /var/log/kingbird/kingbird-api.log &
