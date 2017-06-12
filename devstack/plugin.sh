# Devstack extras script to install Kingbird

# Test if any kingbird services are enabled
# is_kingbird_enabled
function is_kingbird_enabled {
    [[ ,${ENABLED_SERVICES} =~ ,"kb-" ]] && return 0
    return 1
}

# create_kingbird_accounts() - Set up common required kingbird
# service accounts in keystone
# Project               User            Roles
# -------------------------------------------------------------------------
# $SERVICE_TENANT_NAME  kingbird       service

function create_kingbird_accounts {
    if [[ "$ENABLED_SERVICES" =~ "kb-api" ]]; then
        create_service_user "kingbird"

        local kingbird_service=$(get_or_create_service "kingbird" \
            "Kingbird" "OpenStack Kingbird Service")
        get_or_create_endpoint $kingbird_service \
            "$REGION_NAME" \
            "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0" \
            "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0" \
            "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0"
    fi
}

# create_kingbird_cache_dir() - Set up cache dir for kingbird
function create_kingbird_cache_dir {

    # Delete existing dir
    sudo rm -rf $KINGBIRD_AUTH_CACHE_DIR
    sudo mkdir -p $KINGBIRD_AUTH_CACHE_DIR
    sudo chown `whoami` $KINGBIRD_AUTH_CACHE_DIR

}

# init common config-file configuration for kingbird services
# in devstack
# generally the configuration sample file will be generated by
# tox -egen-config
function init_common_kingbird_conf {
    local conf_file=$1

    touch $conf_file
    iniset $conf_file DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $conf_file DEFAULT use_syslog $SYSLOG

    iniset $conf_file cache admin_username admin
    iniset $conf_file cache admin_password $ADMIN_PASSWORD
    iniset $conf_file cache admin_tenant admin
    iniset $conf_file cache project_domain_name Default
    iniset $conf_file cache user_domain_name Default
    iniset $conf_file cache auth_url http://$HOST_IP/identity
    iniset $conf_file cache identity_url http://$HOST_IP/identity
    iniset $conf_file cache auth_uri http://$HOST_IP/identity/v3

    iniset $conf_file database connection `database_connection_url kingbird`
}

function configure_kingbird_api {
    echo "Configuring kingbird api service"

    if is_service_enabled kb-api ; then

        if is_service_enabled keystone; then

            create_kingbird_cache_dir

            # Configure auth token middleware
            configure_auth_token_middleware $KINGBIRD_CONF kingbird \
                $KINGBIRD_AUTH_CACHE_DIR

        else
            iniset $KINGBIRD_CONF DEFAULT auth_strategy noauth
        fi

    fi
}


function configure_kingbird_engine {
    echo "Configuring kingbird engine service"

    if is_service_enabled kb-engine ; then

        # put additional kb-engine configuration here
        echo
    fi
}


if [[ "$Q_ENABLE_KINGBIRD" == "True" ]]; then
    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        echo summary "Kingbird pre-install"
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Kingbird"

        git_clone $KINGBIRD_REPO $KINGBIRD_DIR $KINGBIRD_BRANCH


    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configure Kingbird"

        sudo install -d -o $STACK_USER -m 755 $KINGBIRD_CONF_DIR

        init_common_kingbird_conf $KINGBIRD_CONF

        configure_kingbird_api
        configure_kingbird_engine

        echo export PYTHONPATH=\$PYTHONPATH:$KINGBIRD_DIR >> $RC_DIR/.localrc.auto

        recreate_database kingbird
        python "$KINGBIRD_DIR/kingbird/cmd/manage.py" \
               "--config-file=$KINGBIRD_CONF" db_sync

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Kingbird Service"

        if is_service_enabled kb-engine; then
            run_process kb-engine "python $KINGBIRD_ENGINE --config-file=$KINGBIRD_CONF"
        fi

        if is_service_enabled kb-api; then

            create_kingbird_accounts

            run_process kb-api "python $KINGBIRD_API --config-file $KINGBIRD_CONF"
        fi
    fi

    if [[ "$1" == "unstack" ]]; then

        if is_service_enabled kb-engine; then
           stop_process kb-engine
        fi

        if is_service_enabled kb-api; then
           stop_process kb-api
        fi
    fi
fi
