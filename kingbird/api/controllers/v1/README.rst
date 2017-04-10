=================================================
Example API CURL requests for quota management V1
=================================================

Note:
admin_tenant_id: Tenant ID of admin.
tenant_1: Tenant ID of the project for which we want to perform operation.

===
PUT
===
Creates/Updates quota for a project
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X PUT \
 -d '{"quota_set":{"instances":20,"cores": 20,"ram": 12300,"floating_ips": 50,"metadata_items": 200,"security_groups": 50,"security_group_rules": 50,"key_pairs": 200 }}' \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tenant_1

======
DELETE
======
Can be called only by Admin user

1. To delete all resources for tenant_1 from DB

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X DELETE \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tenant_1

2. To delete resources mentioned in quota_set for tenant_1 from DB

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X DELETE \
 -d '{"quota_set": [ "instances", "floating_ips", "metadata_items", "security_groups", "security_group_rules", "key_pairs"]}' \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tenant_1

===
GET
===
Can be called by both Admin/Non-Admin user

1. To get quota limits for all resources in tenant_1

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tenant_1

2. To get the default quota limits from conf file

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/defaults

3. To get the total resource usages for a tenant

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tanant_1/detail

==========
QUOTA SYNC - for a project
==========
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X PUT \
  http://127.0.0.1:8118/v1.0/admin_tenant_id/os-quota-sets/tenant_1/sync

=======================================================
Example API CURL requests for quota class management V1
=======================================================

===
PUT
===
Can be called only by Admin user

curl \
 -H “Content-Type: application/json” \
 -H “X-Auth-Token: $TOKEN” \
 -H “ROLE: admin” \
 -X PUT -d \
 ‘{“quota_class_set”:{“cores”: 100, “network”:50,”security_group”: 50,”security_group_rule”: 50}}’ \
  http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/$class_name

===
GET
===
Get default quota class

curl \
 -H “Content-Type: application/json” \
 -H “X-Auth-Token: $TOKEN” \
 -H “X_ROLE: admin” \
  http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/$class_name

======
DELETE
======
Delete default quota class

curl \
 -H “Content-Type: application/json” \
 -H “X-Auth-Token: $TOKEN” \
 -H “ROLE: admin” \
 -X DELETE \
  http://$kb_ip_addr:8118/v1.0/$admin_tenant_id/os-quota-class-sets/$class_name

=================================================
Example API CURL requests for quota management V1.1
=================================================

Note:
tenant_id: Tenant ID of the project for which we want to perform operation.

===
PUT
===
Creates/Updates quota for a project
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X PUT \
 -d '{"quota_set":{"instances":20,"cores": 20,"ram": 12300,"floating_ips": 50,"metadata_items": 200,"security_groups": 50,"security_group_rules": 50,"key_pairs": 200 }}' \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets

======
DELETE
======
Can be called only by Admin user

1. To delete all resources for tenant_1 from DB

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X DELETE \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/

2. To delete resources mentioned in quota_set for tenant_1 from DB

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X DELETE \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/?'fixed_ips=15&backups=12'

===
GET
===
Can be called by both Admin/Non-Admin user

1. To get quota limits for all resources in tenant_1

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/

2. To get the default quota limits from conf file

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/defaults

3. To get the total resource usages for a tenant

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/detail

4. To get quota limits for another tenant
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/detail


==========
QUOTA SYNC - for a project
==========
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X PUT \
  http://127.0.0.1:8118/v1.1/tenant_id/os-quota-sets/sync

