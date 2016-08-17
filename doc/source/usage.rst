===================
Kingbird User Guide
===================

Quota management for OpenStack multi-region deployments
-------------------------------------------------------
Kingbird is centralized synchronization service for multi-region OpenStack
deployments. In OPNFV Colorado release, Kingbird provides centralized quota
management feature. Administrator can set quota per project based in Kingbird
and sync the quota limit to multi-region OpenStack periodiclly or on-demand.
The tenant can check the total quota limit and usage from Kingbird for all
regions. Administrator can aslo manage the default quota by quota class
setting.

Following quota items are supported to be managed in Kingbird:

- **instances**: Number of instances allowed per project.
- **cores**: Number of instance cores allowed per project.
- **ram**: Megabytes of instance RAM allowed per project.
- **metadata_items**: Number of metadata items allowed per instance.
- **key_pairs**: Number of key pairs per user.
- **fixed_ips**: Number of fixed IPs allowed per project,
  valid if Nova Network is used.
- **security_groups**: Number of security groups per project,
  valid if Nova Network is used.
- **floating_ips**: Number of floating IPs allowed per project,
  valid if Nova Network is used.
- **network**: Number of networks allowed per project,
  valid if Neutron is used.
- **subnet**: Number of subnets allowed per project,
  valid if Neutron is used.
- **port**: Number of ports allowed per project,
  valid if Neutron is used.
- **security_group**: Number of security groups allowed per project,
  valid if Neutron is used.
- **security_group_rule**: Number of security group rules allowed per project,
  valid if Neutron is used.
- **router**: Number of routers allowed per project,
  valid if Neutron is used.
- **floatingip**: Number of floating IPs allowed per project,
  valid if Neutron is used.
- **volumes**: Number of volumes allowed per project.
- **snapshots**: Number of snapshots allowed per project.
- **gigabytes**: Total amount of storage, in gigabytes, allowed for volumes
  and snapshots per project.
- **backups**: Number of volume backups allowed per project.
- **backup_gigabytes**: Total amount of storage, in gigabytes, allowed for volume
  backups per project.

Only restful APIs are provided for Kingbird in Colorado release, so curl or
other http client can be used to call Kingbird API.

Before use the following command, get token, project id, and kingbird service
endpoint first. Use $kb_token to repesent the token, and $admin_tenant_id as
administrator project_id, and $tenant_id as the target project_id for quota
management and $kb_ip_addr for the kingbird service endpoint ip address.

Note:
To view all tenants (projects), run:

.. code-block:: bash

    openstack project list

To get token, run:

.. code-block:: bash

    openstack token issue

To get Kingbird service endpoint, run:

.. code-block:: bash

    openstack endpoint list

Quota Management API
--------------------

1. Update global limit for a tenant

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "ROLE: dmin" \
   -X PUT \
   -d '{"quota_set":{"cores": 10,"ram": 51200, "metadata_items": 100,"key_pairs": 100, "network":20,"security_group": 20,"security_group_rule": 20}}' \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id

2. Get global limit for a tenant

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id

3. A tenant can also get the global limit by himself

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   http://$kb_ip_addr:8118/v1.0/$tenant_id/os-quota-sets/$tenant_id

4. Get defaults limits

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/defaults

5. Get total usage for a tenant

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   -X GET \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id/detail

6. A tenant can also get the total usage by himself

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -X GET \
   http://$kb_ip_addr:8118/v1.0/$tenant_id/os-quota-sets/$tenant_id/detail

7. On demand quota sync

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   -X PUT \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id/sync


8. Delete specific global limit for a tenant

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   -X DELETE \
   -d '{"quota_set": [ "cores", "ram"]}' \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id

9. Delete all kingbird global limit for a tenant

  curl \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $kb_token" \
  -H  "X_ROLE: admin" \
  -X DELETE \
  http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-sets/$tenant_id


Quota Class API
---------------

1. Update default quota class

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "ROLE: dmin" \
   -X PUT \
   -d '{"quota_class_set":{"cores": 100, "network":50,"security_group": 50,"security_group_rule": 50}}' \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/default

2. Get default quota class

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "X_ROLE: admin" \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/default

3. Delete default quota class

   curl \
   -H "Content-Type: application/json" \
   -H "X-Auth-Token: $kb_token" \
   -H  "ROLE: dmin" \
   -X DELETE \
   http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/default
