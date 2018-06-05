#Configuring the pillars dynamically
admin_tenant_details:
  cmd.run:
    - name: salt '*' keystoneng.project_get name=admin > /srv/salt/admin_tenant_details.txt
pillars_configuration_permissions:
  file:
    - managed
    - name: "/srv/salt/pillars_configuration.sh"
    - user: root
    - group: root
    - mode: 777
pillars_configuration:
  cmd.run:
    - name: "/srv/salt/pillars_configuration.sh"
    - cwd: /srv/pillar
