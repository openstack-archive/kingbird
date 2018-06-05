#Purpose of Keystoneng module is to perform Keystone related operations.
#Keystoneng needs to be configured in /etc/salt/minion.
#Once it is configured,Restart the minion configuration file
keystone_configuration_permissions:
  file:
    - managed
    - name: "/srv/salt/keystone_configuration.sh"
    - user: root
    - group: root
    - mode: 777
keystone_configuration:
  cmd.run:
    - name: "/srv/salt/keystone_configuration.sh"
    - cwd: /srv/salt
/etc/salt/minion:
  file:
    - append
    - source : /srv/salt/keystone_details.txt
