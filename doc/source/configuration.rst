============================
Kingbird Configuration Guide
============================

A brief introduction to configure Multisite Kingbird service. Only the
configuration items for Kingbird will be described here. Logging,
messaging, database, keystonemiddleware etc configuration which are
generated from OpenStack OSLO libary, will not be described here, for
these configuration items are common to Nova, Cinder, Neutron. So please
refer to corresponding description from Nova or Cinder or Neutron.


Configuration in [DEFAULT]
--------------------------

configuration items for kingbird-api
""""""""""""""""""""""""""""""""""""

bind_host
*********
- default value: *bind_host = 0.0.0.0*
- description: The host IP to bind for kingbird-api service

bind_port
*********
- default value: *bind_port = 8118*
- description: The port to bind for kingbird-api service

api_workers
***********
- default value: *api_workers = 2*
- description: Number of kingbird-api workers

configuration items for kingbird-engine
"""""""""""""""""""""""""""""""""""""""

host
****
- default value: *host = localhost*
- description: The host name kingbird-engine service is running on

workers
*******
- default value: *workers = 1*
- description: Number of kingbird-engine workers

report_interval
***************
- default value: *report_interval = 60*
- description: Seconds between running periodic reporting tasks to
  keep the engine alive in the DB. If the engine doesn't report its
  aliveness to the DB more than two intervals, then the lock accquired
  by the engine will be removed by other engines.

common configuration items for kingbird-api and kingbird-engine
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

use_default_quota_class
***********************
- default value: *use_default_quota_class = true*
- description: Enables or disables use of default quota class with default
  quota, boolean value

Configuration in [kingbird_global_limit]
----------------------------------------

For quota limit, a negative value means unlimited.

configuration items for kingbird-api and kingbird-engine
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

quota_instances
***************
- default value: *quota_instances = 10*
- description: Number of instances allowed per project, integer value.

quota_cores
***********
- default value: *quota_cores = 20*
- description: Number of instance cores allowed per project, integer value.

quota_ram
*********
- default value: *quota_ram = 512*
- description: Megabytes of instance RAM allowed per project, integer value.

quota_metadata_items
********************
- default value: *quota_metadata_items = 128*
- description: Number of metadata items allowed per instance, integer value.

quota_key_pairs
***************
- default value: *quota_key_pairs = 10*
- description: Number of key pairs per user, integer value.

quota_fixed_ips
***************
- default value: *quota_fixed_ips = -1*
- description: Number of fixed IPs allowed per project, this should be at
  least the number of instances allowed, integer value.

quota_security_groups
*********************
- default value: *quota_security_groups = 10*
- description: Number of security groups per project, integer value.

quota_floating_ips
******************
- default value: *quota_floating_ips = 10*
- description: Number of floating IPs allowed per project, integer value.

quota_network
***************
- default value: *quota_network = 10*
- description: Number of networks allowed per project, integer value.

quota_subnet
***************
- default value: *quota_subnet = 10*
- description: Number of subnets allowed per project, integer value.

quota_port
***************
- default value: *quota_port = 50*
- description: Number of ports allowed per project, integer value.

quota_security_group
********************
- default value: *quota_security_group = 10*
- description: Number of security groups allowed per project, integer value.

quota_security_group_rule
*************************
- default value: *quota_security_group_rule = 100*
- description: Number of security group rules allowed per project, integer
  value.

quota_router
************
- default value: *quota_router = 10*
- description: Number of routers allowed per project, integer value.

quota_floatingip
****************
- default value: *quota_floatingip = 50*
- description: Number of floating IPs allowed per project, integer value.

quota_volumes
***************
- default value: *quota_volumes = 10*
- description: Number of volumes allowed per project, integer value.

quota_snapshots
***************
- default value: *quota_snapshots = 10*
- description: Number of snapshots allowed per project, integer value.

quota_gigabytes
***************
- default value: *quota_gigabytes = 1000*
- description: Total amount of storage, in gigabytes, allowed for volumes
  and snapshots per project, integer value.

quota_backups
*************
- default value: *quota_backups = 10*
- description: Number of volume backups allowed per project, integer value.

quota_backup_gigabytes
**********************
- default value: *quota_backup_gigabytes = 1000*
- description: Total amount of storage, in gigabytes, allowed for volume
  backups per project, integer value.

Configuration in [cache]
----------------------------------------

The [cache] section is used by kingbird engine to access the quota
information for Nova, Cinder, Neutron in each region in order to reduce
the KeyStone load while retrieving the endpoint information each time.

configuration items for kingbird-engine
"""""""""""""""""""""""""""""""""""""""

auth_uri
***************
- default value:
- description: Keystone authorization url, for example, http://127.0.0.1:5000/v3.

admin_username
**************
- default value:
- description: Username of admin account, for example, admin.

admin_password
**************
- default value:
- description: Password for admin account, for example, password.

admin_tenant
************
- default value:
- description: Tenant name of admin account, for example, admin.

admin_user_domain_name
**********************
- default value: *admin_user_domain_name = Default*
- description: User domain name of admin account.

admin_project_domain_name
*************************
- default value: *admin_project_domain_name = Default*
- description: Project domain name of admin account.

Configuration in [scheduler]
----------------------------------------

The [scheduler] section is used by kingbird engine to periodically synchronize
and rebalance the quota for each project.

configuration items for kingbird-engine
"""""""""""""""""""""""""""""""""""""""

periodic_enable
***************
- default value: *periodic_enable = True*
- description: Boolean value for enable/disable periodic tasks.

periodic_interval
*****************
- default value: *periodic_interval = 900*
- description: Periodic time interval for automatic quota sync job, unit is
  seconds.

Configuration in [batch]
----------------------------------------

The [batch] section is used by kingbird engine to periodicly synchronize
and rebalance the quota for each project.

batch_size
***************
- default value: *batch_size = 3*
- description: Batch size number of projects will be synced at a time.

Configuration in [locks]
----------------------------------------

The [locks] section is used by kingbird engine to periodically synchronize
and rebalance the quota for each project.

lock_retry_times
****************
- default value: *lock_retry_times = 3*
- description: Number of times trying to grab a lock.

lock_retry_interval
*******************
- default value: *lock_retry_interval =10*
- description: Number of seconds between lock retries.
