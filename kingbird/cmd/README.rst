===============================
cmd
===============================

Scripts to start the Kingbird API and Engine services

api.py:
    start API service
    python api.py --config-file=/etc/kingbird.conf

engine.py:
    start Engine service
    python engine.py --config-file=/etc/kingbird.conf

manage.py:
    CLI interface for kingbird management
    kingbird-manage --config-file /etc/kingbird.conf db_sync
    kingbird-manage --config-file /etc/kingbird.conf db_version