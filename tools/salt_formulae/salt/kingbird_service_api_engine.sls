run_api:
  cmd.run:
    - name: 'python {{ grains.get('kingbird_path') }}{{ pillar.get('api_script') }} &'
    - bg: True
run_engine:
  cmd.run:
    - parallel: True
    - name: 'python {{ grains.get('kingbird_path') }}{{ pillar.get('engine_script') }} &'
    - bg: True
