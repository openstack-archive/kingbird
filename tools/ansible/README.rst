=======================
Kingbird Ansible Guide
=======================

Boostrap Kingbird Service
--------------------------
This Playbook helps in setting up Kingbird in OpenStack i.e creating a user, service and Endpoints.

Initial requirements
---------------
Linux machine with Ansible Installed

Installation instruction
------------------------

.. code-block:: bash

    source openrc
    ansible-playbook kingbird_bootstrap_bkp.yml

This will do the Following Operations:

.. code-block:: bash

    1 - Create a Openstack Service `Kingbird`.
    2 - Create Endpoints for the created Service.
    3 - Create a user Kingbird.
    4 -  Assign role to created user Kingbird.

Things To be covered:

.. code-block:: bash

    1 - Setup Database for Kingbird.
    2 - Generate Kingbird configuration.
    3 - Hassle free easy to setup Kingbird ansible-Playbook for KB-API and KB-Engine.
