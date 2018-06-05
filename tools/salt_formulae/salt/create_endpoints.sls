kingbird_user:
  keystone_user.present:
    - name: kingbird
    - password: password
    - domain_id: default
kingbird_role_grant:
  keystone_role_grant.present:
    - role: admin
    - user: kingbird
    - project: service
kingbird_service:
  keystone_service.present:
    - name: synchronization
    - type: kingbird
kingbird_public_endpoint:
  keystone_endpoint.present:
    - name: public
    - url: http://192.168.122.167:8118/v1.0
    - region: RegionOne
    - service_name: kingbird
kingbird_admin_endpoint:
  keystone_endpoint.present:
    - name: admin
    - url: http://192.168.122.167:8118/v1.0
    - region: RegionOne
    - service_name: kingbird
kingbird_internal_endpoint:
  keystone_endpoint.present:
    - name: internal
    - url: http://192.168.122.167:8118/v1.0
    - region: RegionOne
    - service_name: kingbird
