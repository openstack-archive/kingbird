Tests for Kingbird in Tempest
====================================

How to run
----------

Get the latest kingbird resources from the appropriate mirror:

.. sourcecode:: console

    $ git clone https://github.com/openstack/kingbird.git
..

Install kingbird, in order to register the tempest plugin interface:

.. sourcecode:: console

    $ cd kingbird
    $ python setup.py install
..

Get the latest tempest resources from the appropriate mirror:

.. sourcecode:: console

    $ git clone https://github.com/openstack/tempest.git
..

Create a configuration file ``tempest/etc/tempest.conf`` for tempest.
The sample file can be generated and used for this purpose:

.. sourcecode:: console

    $ cd $TEMPEST_ROOT_DIR
    $ tox -e genconfig
    $ cp etc/tempest.conf.sample etc/tempest.conf
..

Some configuration options are required for running tests. Here is the list:

.. sourcecode:: ini

    [auth]
    admin_username=
    admin_project_name=
    admin_password=
    admin_domain_name=

    [identity]
    uri=
    uri_v3=
    auth_version=
    username=
    password=
    region=
    tenant_name=
    domain_name=
    alt_domain_name=
    default_domain_id=

    [compute]
    image_ref=

..

All the parameters above are defined by tempest.

The parameters which are only specific to kingbird tempest plugin
are configured in kingbird/tests/tempest/scenario/config.py by group name KBGroup.

..
    endpoint_type=publicURL
    TIME_TO_SYNC=30
    endpoint_url=http://127.0.0.1:8118/
    api_version=v1.0

..

When configuration is finished, you can list the testcases in Kingbird plugin:

.. sourcecode:: console

    $ testr list-tests | grep kingbird
..


If you want to launch the tests from tempest, you can do with:

.. sourcecode:: console

    $ tox -e all-plugin -- scenario.quota_management.client_tests
..

If you want to launch all Kingbird tests in Tempest, you can do this with ``quota_management`` tag:

.. sourcecode:: console

    $ tox -e all-plugin -- quota_management
..

If you want to launch a single Kingbird testcase in Tempest, you can do this with:

.. sourcecode:: console

    $ tox -e all-plugin scenario.quota_management.client_tests.test_quota_management_api.KingbirdQMTestJSON.test_kingbird_delete_method
..
