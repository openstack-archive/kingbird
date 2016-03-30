==============================
Tempest Integration of Kingbird
==============================

This directory contains Tempest tests to cover the kingbird project.

Before running Tempest test cases, Do the following

1. Clone tempest code from git

2. Make below changes in tempest/config.py

I) Add kingbird configurations to config file::

    kb_group = cfg.OptGroup(name='kingbird',
                            title="Options for kingbird configurations")

    KBOpts = [
        cfg.StrOpt('endpoint_type',
                   default='publicURL',
                   help="Endpoint type of Kingbird service."),
        cfg.StrOpt('endpoint_url',
                   help="Endpoint URL of Kingbird service."),
        cfg.StrOpt('api_version',
                   default='v1.0',
                   help="Api version of Kingbird service.")
    ]

II) Add kingbird service to ServiceAvailableGroup as below::
    cfg.BoolOpt('kingbird',
                default=False,
                help="Whether or not kingbird is expected to be available"),

III) Add kb_group and KBOpts to list of opts(_opts)

3. Generate config file::
    $ tox -e genconfig

   It generates etc/tempest.conf.sample. Copy it to /etc/tempest/ and rename as tempest.conf

4. Copy tempest testcases for Kingbird::

    $ cp -r kingbird_tempest_tests/tests/api/kingbird/ <tempest root directory>/tempest/api/
    $ cp kingbird_tempest_tests/tests/common/kingbird.py <tempest root directory>/tempest/common/

To list all Kingbird tempest cases, go to tempest directory, then run::

   $ testr list-tests kingbird

To run kingbird tempest with nosetests, go to tempest directory, then run::
   $ nosetests -sv tempest/api/kingbird/test_kingbird_api.py

To run kingbird tempest plugin tests using tox, go to tempest directory, then run::

   $ tox -eall-plugin kingbird

To run a specific test::

   $ tox -eall-plugin tempest.api.kingbird.test_kingbird_api.KingbirdTestJSON.test_kingbird_delete_all_method

To run tempest with run_test, go to tempest directory, then run::

   $ ./run_tempest.sh -N -- kingbird

To run a single test case, go to tempest directory, then run with test case name, e.g.::

   $ ./run_tempest.sh -N -- tempest.api.kingbird.test_kingbird_api.KingbirdTestJSON.test_kingbird_delete_all_method
