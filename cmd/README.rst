===============================
cmd
===============================

Scripts to start the API, JobDaemon and JobWorker service

api.py:
    start API service
    python api.py --config-file=../etc/api.conf

jobdaemon.py:
    start JobDaemon service
    python jobdaemon.py --config-file=../etc/jobdaemon.conf

jobworker.py:
    start JobWorker service
    python jobworker.py --config-file=../etc/jobworker.conf
