base:
  '*':
    - configure_keystone
    - configure_pillars
    - configure_kingbird
    - create_endpoints
    - create_database
    - kingbird_service_api_engine
