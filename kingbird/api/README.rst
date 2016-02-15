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

====
POST
====

curl -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X POST --data "{'tenant_1': {'ram':15, 'cores':12}, 'tenant_2':{'cpu':15}}"  http://127.0.0.1:8118/v1.0/quota_manager

===
PUT
===

curl -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X PUT --data "{'tenant_1': {'ram':10, 'cores':20}, 'tenant_2': {'cpu':20}}"  http://127.0.0.1:8118/v1.0/quota_manager

======
DELETE
======

curl -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X DELETE --data "{'tenant_1': ['ram', 'cores'], 'tenant_2': 'all'}"  http://127.0.0.1:8118/v1.0/quota_manager

===
GET
===

curl -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" http://127.0.0.1:8118/v1.0/quota_manager/?project_id=tenant_1\&resource=ram

curl -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" http://127.0.0.1:8118/v1.0/quota_manager/?project_id=tenant_1
