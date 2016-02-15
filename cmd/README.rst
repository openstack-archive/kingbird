===============================
cmd
===============================

Scripts to start the API, JobDaemon and JobWorker service

api.py:
    start API service
    python api.py --config-file=../etc/api.conf

engine.py:
    start Engine service
    python engine.py --config-file=../etc/engine.conf

manage.py:
    CLI interface for kingbird management
    python manage.py ../etc/api.conf
