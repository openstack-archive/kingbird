===============================
devstack
===============================

Scripts to integrate the API, JobDaemon and JobWorker service to OpenStack
devstack development environment

local.conf.sample:
    sample configruation to integrate kingbird into devstack
    cuntomize the configuration file to tell devstack which OpenStack services
    will be launched

plugin.sh: plugin to the devstack
    devstack will automaticly search the devstack folder, and load, exeucte
    the plugin.sh in different environment establishment phase

settins: configuration for kingbird in the devstack
    devstack will automaticly load the settings to be used in the plugin.sh
