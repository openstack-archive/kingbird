===============================
Service
===============================

Kingbird Service has responsibility for:
    Delegate the task to concerned engine component managed by a EngineManager
    in listener.py

    Monitoring the job/smaller jobs status, and return the result to Kingbird
    API if needed.

    Generate task to purge time-out jobs from Kingbird Database

    Multiple Kingbird API could run in parallel, and also can work in
    multi-worker mode.

    Multiple Kingbird Daemon will be designed and run in stateless mode,
    persistent data will be accessed (read and write) from the Kingbird
    Database through the DAL module.

service.py:
    run KB service in multi-worker mode, and establish RPC server

listener.py
    Manages all engine side activities such as Quota Enforcement,
    synchronisation of ssh keys, images, flavors, security groups,
    etc. across regions

engine_cfg.py:
    configuration and initialization for Engine service
