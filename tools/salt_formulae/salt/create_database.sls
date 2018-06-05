{{ pillar.get('service_name') }}:
  mysql_database.present:
   - grant: all privileges
   - connection_user: root
   - connection_pass: {{ grains.get('database_password') }}
   - connection_host: localhost
   - connection_charset: utf8
migrationscripts:
   cmd.run:
     - connection_user: root
     - connection_pass: {{ grains.get('database_password') }}
     - name: 'python {{ grains.get('kingbird_path') }}{{ pillar.get('migration_script') }} db_sync'
