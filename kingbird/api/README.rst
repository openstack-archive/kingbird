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

enforcer.py
    Enforces policies on the version2 API's
