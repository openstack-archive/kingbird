Kingbird installation with Salt Guide
=====================================

This Guide will help in configuring kingbird and fill out necessary fields in 
kingbird.conf file using salt formulae 

Introduction to SaltStack
=========================

Salt is a new approach to infrastructure management built on a dynamic communication bus.
Salt can be used for data-driven orchestration, remote execution for any infrastructure,
configuration management for any app stack, and much more.

Installation
-------------

* `Salt`_ - Salt installation

.. _Salt: https://docs.saltstack.com/en/getstarted/system/index.html

Steps to configure kingbird:
===========================

Firstly, fill out the parameters under [Default] section::

   For eg::
     bind_host = 0.0.0.0
     bind_port = 8118

and the absolute path of `manage.py` which executes the migration scripts::

   For eg::
     migration_script: '/home/r1/kingbird/kingbird/cmd/manage.py'

Secondly, fill out the values which are under the section [cache]
values filled out here are used for the periodic balance cron job::

   For eg:
     cache_auth_uri=http://172.16.69.145/identity
     cache_admin_username=admin
     cache_admin_password=****
     cache_admin_tenant=7523912b8970459c9d9f9dd548ba6aa9
     cache_admin_user_domain_name=Default
     cache_admin_project_domain_name=Default

Thirdly, fill out the values which are under the section [database]
values filled out here are used for database connection. we can 
configure database to MYSQL or SQLite::

   For eg::
     database_type: 'mysql'
     database_type: 'sqlite'

If database type is Mysql mention the password of mysql::

   For eg::
     database_password: '***'

Next, Fill out the feilds under the section [keystone_authtoken]::

   For eg::
     auth_token_keystone_memcached__servers: '172.16.69.145:11211'
     auth_token_project_domain_name : 'Default'
     auth_token_project_name : 'service'
     auth_token_user_domain_name : 'Default'
     auth_token_password : 'openstack'
     kingbird_username : 'kingbird'
     auth_token_auth_url : 'http://172.16.69.145/identity'
     auth_token_auth_type : 'password'

Fourthly, fillout  the global limits for kingbird::

   For eg::
      global_quota_instances : 10
      global_quota_cores : 20
      global_quota_ram : 51200
      global_quota_floating_ips : 10
      global_quota_fixed_ips : -1
      global_quota_metadata_items : 128
      global_quota_security_groups : 10
      global_quota_key_pairs : 100
      global_quota_network : 10
      global_quota_subnet : 10
      global_quota_port : 50
      global_quota_security_group : 10
      global_quota_security_group_rule : 100
      global_quota_router : 10
      global_quota_floatingip : 50
      global_quota_volumes : 10
      global_quota_snapshots : 10
      global_quota_gigabytes : 1000
      global_quota_backups : 10
      global_quota_backup_gigabytes : 1000

Once we are done with these steps we can execute our kingbird salt formulae
apply the salt state using::

   salt '*' state.apply
