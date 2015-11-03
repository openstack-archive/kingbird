# Devstack extras script to install Tricircle

# Test if any kingbird services are enabled
# is_kingbird_enabled
function is_kingbird_enabled {
    [[ ,${ENABLED_SERVICES} =~ ,"kb-svc-" ]] && return 0
    return 1
}

# create_kingbird_accounts() - Set up common required kingbird
# service accounts in keystone
# Project               User            Roles
# -------------------------------------------------------------------------
# $SERVICE_TENANT_NAME  kingbird       service

function create_kingbird_accounts {
    if [[ "$ENABLED_SERVICES" =~ "kb-svc-api" ]]; then
        create_service_user "kingbird"

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
            local kingbird_service=$(get_or_create_service "kingbird" \
                "Kingbird" "OpenStack Kingbird Service")
            get_or_create_endpoint $kingbird_service \
                "$REGION_NAME" \
                "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0" \
                "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0" \
                "$SERVICE_PROTOCOL://$KINGBIRD_API_HOST:$KINGBIRD_API_PORT/v1.0"
        fi
    fi
}

# create_kingbird_cache_dir() - Set up cache dir for kingbird
function create_kingbird_cache_dir {

    # Delete existing dir
    sudo rm -rf $KINGBIRD_AUTH_CACHE_DIR
    sudo mkdir -p $KINGBIRD_AUTH_CACHE_DIR
    sudo chown `whoami` $KINGBIRD_AUTH_CACHE_DIR

}


function configure_kingbird_api {
    echo "Configuring kingbird api service"

    if is_service_enabled kb-svc-api ; then
        cp -p $KINGBIRD_DIR/etc/api.conf $KINGBIRD_API_CONF
        iniset $KINGBIRD_API_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
        iniset $KINGBIRD_API_CONF DEFAULT verbose True
        iniset $KINGBIRD_API_CONF DEFAULT use_syslog $SYSLOG

        setup_colorized_logging $KINGBIRD_API_CONF DEFAULT

        if is_service_enabled keystone; then

            create_kingbird_cache_dir

            # Configure auth token middleware
            configure_auth_token_middleware $KINGBIRD_API_CONF kingbird \
                $KINGBIRD_AUTH_CACHE_DIR

        else
            iniset $KINGBIRD_API_CONF DEFAULT auth_strategy noauth
        fi

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

        configure_kingbird_api

        echo export PYTHONPATH=\$PYTHONPATH:$KINGBIRD_DIR >> $RC_DIR/.localrc.auto

        recreate_database kingbird
        # python "$KINGBIRD_DIR/cmd/manage.py" "$KINGBIRD_CONF"

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Kingbird Service"

        if is_service_enabled kb-svc-jw; then
            run_process kb-svc-jw "python $KINGBIRD_JW_SERVICE --config-file $KINGBIRD_JW_CONF --config-dir $KINGBIRD_CONF_DIR"
        fi

        if is_service_enabled kb-svc-jd; then
            run_process kb-svc-jd "python $KINGBIRD_JD_SERVICE --config-file $KINGBIRD_JD_CONF --config-dir $KINGBIRD_CONF_DIR"
        fi

        if is_service_enabled kb-svc-api; then

            create_kingbird_accounts

            run_process kb-svc-api "python $KINGBIRD_API --config-file $KINGBIRD_API_CONF"
        fi
    fi

    if [[ "$1" == "unstack" ]]; then

        if is_service_enabled kb-svc-jw; then
           stop_process kb-svc-jw
        fi

        if is_service_enabled kb-svc-jd; then
           stop_process kb-svc-jd
        fi

        if is_service_enabled kb-svc-api; then
           stop_process kb-svc-api
        fi
    fi
fi
