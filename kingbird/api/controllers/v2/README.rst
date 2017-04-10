=================================================
Example API CURL requests for quota management V2
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
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets

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
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/

2. To delete resources mentioned in quota_set for tenant_1 from DB

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X DELETE \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/?'fixed_ips=15&backups=12'

===
GET
===
Can be called by both Admin/Non-Admin user

1. To get quota limits for all resources in tenant_1

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/

2. To get the default quota limits from conf file

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/defaults

3. To get the total resource usages for a tenant

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/detail

4. To get quota limits for another tenant
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/detail


==========
QUOTA SYNC - for a project
==========
Can be called only by Admin user

curl \
 -H "Content-Type: application/json" \
 -H "X-Auth-Token: $TOKEN" \
 -H  "X_ROLE: admin" \
 -X PUT \
  http://127.0.0.1:8118/v2.0/tenant_id/os-quota-sets/sync
