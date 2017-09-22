{{ pillar.get('service_name') }}:
  mysql_database.present:
   - grant: all privileges
   - connection_user: root
   - connection_pass: {{ pillar.get('database_password') }}
   - connection_host: localhost
   - connection_charset: utf8

migrationscripts:
   cmd.run:
     - name: 'python {{ pillar.get('migration_script') }} db_sync'
