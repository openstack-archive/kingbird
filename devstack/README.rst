===============================
devstack
===============================

Scripts to integrate the API and Engine service to OpenStack
devstack development environment

local.conf.sample:
    sample configuration to integrate kingbird into devstack
    customize the configuration file to tell devstack which OpenStack services
    will be launched

plugin.sh: plugin to the devstack
    devstack will automatically search the devstack folder, and load, execute
    the plugin.sh in different environment establishment phase

settings: configuration for kingbird in the devstack
    devstack will automatically load the settings to be used in the plugin.sh
