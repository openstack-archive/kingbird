===============================
api
===============================

Kingbird API is Web Server Gateway Interface (WSGI) applications to receive
and process API calls, including keystonemiddleware to do the authentication,
parameter check and validation, convert API calls to job rpc message, and
then send the job to Kingbird Engine through the queue. If the job will
be processed by Kingbird Engine in synchronous way, the Kingbird API will
wait for the response from the Kingbird Engine. Otherwise, the Kingbird
API will send response to the API caller first, and then send the job to
Kingbird Engine in asynchronous way.

Multiple Kingbird API could run in parallel, and also can work in multi-worker
mode.

Multiple Kingbird API will be designed and run in stateless mode, persistent
data will be accessed (read and write) from the Kingbird Database through the
DAL module.

Setup and encapsulate the API WSGI app

app.py:
    Setup and encapsulate the API WSGI app, including integrate the
    keystonemiddleware app

apicfg.py:
    API configuration loading and init

==============================================
Example API CURL requests for quota management
==============================================

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
