===============================
jobworker
===============================

Kingbird Job Worker has responsibility for:
    Concurrently process the divided smaller jobs from Kingbird Job Daemon.
    Each smaller job will be a job to a specific OpenStack instance, i.e.,
    one OpenStack region.

    Periodically running background job which was assigned by the Kingbird
    Job Daemon, Kingbird Job Worker will generate a new one-time job (for
    example, for quota enforcement, generate a collecting resource usage job),
    and send it to the Kingbird Job Daemon for further processing in each
    cycle. Multiple Job Worker could run in parallel, and also can work in
    multi-worker mode. But for one smaller job from Kingbird  Job Daemon,
    only one Kingbird Job Worker will be the owner. One Kingbird Job Worker
    could be the owner of multiple smaller jobs from multiple Kingbird
    JobDaemons.

    Multiple Kingbird Job Workers will be designed and run in stateless mode,
    persistent data will be accessed (read and write) from the Kingbird
    Database through the DAL module.

jwrpcapi.py:
    the client side RPC api for JobWoker. Often the JobDaemon service will
    call the api provided in this file, and the RPC client will send the
    request to message-bus, and then the JobWorker can pickup the RPC message
    from the message bus

jwservice.py:
    run JobWorker in multi-worker mode, and establish RPC server

jwmanager.py:
    all rpc messages received by the jwservice RPC server will be processed
    in the jwmanager's regarding function.

jwcfg.py:
    configuration and initialization for JobWorker