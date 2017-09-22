kingbird-conf:
  file:
    - managed
    - name: "/etc/kingbird/kingbird.conf"
    - source: {{pillar.get('sample_kb_conf_file')}}
    - user: root
    - group: root
    - mode: 777
  ini:
    - options_present
    - name: "/etc/kingbird/kb_2.conf"
    - sections:
        DEFAULT:
          bind_host: {{pillar.get('bind_host')}}
          bind_port: {{pillar.get('bind_port')}}
        cache:
            auth_uri: {{pillar.get('cache_auth_uri')}}
            admin_username: {{pillar.get('cache_admin_username')}}
            admin_password: {{pillar.get('cache_admin_password')}}
            admin_tenant: {{pillar.get('cache_admin_tenant_id')}}
            admin_user_domain_name: {{pillar.get('cache_admin_user_domain_name')}}
            admin_project_domain_name: {{pillar.get('cache_admin_project_domain_name')}}
        database:
            {% if pillar.get('database_type') == 'mysql' %}
                connection: mysql+pymysql://root:{{pillar.get('database_password')}}@127.0.0.1/kingbird
            {% elif pillar.get('database_type') == 'sqlite' %}
                connection: sqlite:///{{pillar.get('service_name')}}.db
            {% else%}
                connection: ''
            {% endif%}
        keystone_authtoken:
            memcached_servers: {{pillar.get('auth_token_keystone_memcached__servers')}}
            project_domain_name: {{pillar.get('auth_token_project_domain_name')}}
            project_name: {{pillar.get('auth_token_project_name')}}
            user_domain_name: {{pillar.get('auth_token_user_domain_name')}}
            password: {{pillar.get('auth_token_password')}}
            username: {{pillar.get('kingbird_username')}}
            auth_uri: {{pillar.get('auth_token_auth_url')}}
            auth_type: {{pillar.get('auth_token_auth_type')}}
        kingbird_global_limit:
            quota_instances : {{pillar.get('global_quota_instances')}}
            quota_cores : {{pillar.get('global_quota_cores')}}
            quota_ram : {{pillar.get('global_quota_ram')}}
            quota_floating_ips : {{pillar.get('global_quota_floating_ips')}}
            quota_fixed_ips : {{pillar.get('global_quota_fixed_ips')}}
            quota_metadata_items : {{pillar.get('global_quota_metadata_items')}}
            quota_security_groups : {{pillar.get('global_quota_security_groups')}}
            quota_key_pairs : {{pillar.get('global_quota_key_pairs')}}
            quota_network : {{pillar.get('global_quota_network')}}
            quota_subnet : {{pillar.get('global_quota_subnet')}}
            quota_port : {{pillar.get('global_quota_port')}}
            quota_security_group : {{pillar.get('global_quota_security_group')}}
            quota_security_group_rule : {{pillar.get('global_quota_security_group_rule')}}
            quota_router : {{pillar.get('global_quota_router')}}
            quota_floatingip : {{pillar.get('global_quota_floatingip')}}
            quota_volumes : {{pillar.get('global_quota_volumes')}}
            quota_snapshots : {{pillar.get('global_quota_snapshots')}}
            quota_gigabytes : {{pillar.get('global_quota_gigabytes')}}
            quota_backups : {{pillar.get('global_quota_backups')}}
            quota_backup_gigabytes : {{pillar.get('global_quota_backup_gigabytes')}}
