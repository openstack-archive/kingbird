===============================
jobdaemon
===============================

Kingbird Job Daemon has responsibility for:
    Divid job from Kingbird API to smaller jobs, each smaller job will only
    be involved with one specific region, and one smaller job will be
    dispatched to one Kingbird Job Worker. Multiple smaller jobs may be
    dispatched to the same Kingbird Job Worker, it’s up to the load balancing
    policy and how many Kingbird Job Workers are running.

    Some job from Kingbird API  could not be divided, schedule and re-schedule
    such kind of  (periodically running, like quota enforcement, regular
    event statistic collection task)  job to a specific Kingbird Job Worker.
    If some Kingbird Job Worker failed, re-balance the job to other Kingbird
    Job Workers.

    Monitoring the job/smaller jobs status, and return the result to Kingbird
    API if needed.

    Generate task to purge time-out jobs from Kingbird Database

    Multiple Job Daemon could run in parallel, and also can work in
    multi-worker mode. But for one job from Kingbird API, only one Kingbird
    Job Daemon will be the owner. One Kingbird Job Daemon could be the owner
    of multiple jobs from multiple Kingbird APIs

    Multiple Kingbird Daemon will be designed and run in stateless mode,
    persistent data will be accessed (read and write) from the Kingbird
    Database through the DAL module.

jdrpcapi.py:
    the client side RPC api for JobDaemon. Often the API service will
    call the api provided in this file, and the RPC client will send the
    request to message-bus, and then the JobDaemon can pickup the RPC message
    from the message bus

jdservice.py:
    run JobDaemon in multi-worker mode, and establish RPC server

jdmanager.py:
    all rpc messages received by the jdservice RPC server will be processed
    in the jdmanager's regarding function.

jdcfg.py:
    configuration and initialization for JobDaemon