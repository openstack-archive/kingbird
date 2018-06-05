Kingbird installation with Salt Guide
=====================================

This Guide will help in installing Kingbird using salt formulae.

Introduction to SaltStack
=========================

Salt is a new approach to infrastructure management built on a dynamic communication bus.
Salt can be used for data-driven orchestration, remote execution for any infrastructure,
configuration management for any app stack, and much more.

Installation
-------------

* `Salt`_ - Salt installation

.. _Salt: https://docs.saltstack.com/en/getstarted/system/index.html

Steps to installation of kingbird Salt-formulae:
================================================

1. Provide Environment Variables:
   ==============================
   $source openrc admin admin
   Make sure "env|grep OS" is working fine.

2. Clone Kingbird repository:
   ==========================
   $ git clone https://github.com/openstack/kingbird.git
   $ cd kingbird
   /kingbird$ pip install -r requirements.txt
   /kingbird$ python setup.py install
   /kingbird$ cd tools/salt_formulae
   /kingbird/tools/salt_formulae$ cp -r * /srv/

3. Clone Kingbird-client repository:
   ================================
   $ git clone https://github.com/openstack/python-kingbirdclient.git
   $ cd python-kingbirdclient
   $ pip install -r requirements.txt
   $ python setup.py install

4. User have to create grains for database_type and database_password.
   ===================================================================

   Example:
    =========

   /srv/salt/$ salt '*' grains.setvals "{'database_type': 'mysql', 'database_password': 'password'}"

   where:
       database_type    :  The database which the user want's to choose.
                           Kingbird Supports both mysql and sqlite databases.
       database_password:  The password used for the database.

5. User have to create a grain for "kingbird_path"
   ===============================================


   /srv/salt/$ salt '*' grains.setval kingbird_path value

   where the value is the "path to Cloned Kingbird directory".

   Example:
   ========

   /srv/salt$ salt '*' grains.setval kingbird_path /root/


5. Execute the following commands to install:
   =======================================
   Go to your kingbird cloned directory/tools/salt_formulae/salt
   and execute these steps:

   -> salt-call state.sls configure_keystone
   -> Restart master and minion by using:
          service salt-master restart
          service salt-minion restart
   -> salt-call state.sls configure_pillars
   -> salt '*' state.apply exclude="['configure_keystone','configure_pillars']"

6. Execute the Kingbird Commands:
   ==============================

   Example:
   ========
      kingbird sync list
