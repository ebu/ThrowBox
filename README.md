A distributed, virtualized, shell script runner. Has the side effect to be a test_runner.
It will spawn a vm, run shell script, return the result of the run, and destroy the vm, so 
you have time to do something else in the meantime.
It can also use amazon or amazon compatible api to spawn the vm.
This software is in dev status.


Dependencies
============
* [python-vagrant](https://github.com/todddeluca/python-vagrant)
    Used to start vm, querying the host and the port of the vm

* [boto](https://github.com/boto/boto)
    Used to start a ec2 instance and manage it.
    
* [celery](https://github.com/celery/celery)
    Used to remotely start a job

* [fabric](https://github.com/fabric/fabric)
    Used to launch scripts on the vm

Install
=======
Setup on linux
==============
You can install the whole script using setuptool. If you don't have it already, you can install it. It is available in you repository :

    sudo apt-get install python-distribute

or using pip.

    pip install distribute

Then you will need vagrant to be installed, it should be in your repository for example if you use debian:

    sudo apt-get install vagrant

If it's not in your repository, you can use the windows url.

Setup on windows
================
if you are using windows, you can install the lastest version using this url:

    http://downloads.vagrantup.com/

You will also need virtualbox installed. You can find virtualbox at this url:

    https://www.virtualbox.org/wiki/Downloads

Setup the configuration
=======================
You can now edit the config.py to the the values you may want to use.Those entries are document in the default config.py shipped with the software.
You will need a Vagrantfile. A default one is also shipped with the software in base_template/ubuntu-12.04, so you can simply change the config.py VAGRANT_TEMPLATE_DIR to this repository

Usage
=====
Local
=====
You can use the tester locally by using the test_box api. You need first to setup the place 
where the vagrant configurations are stored. This key is hosted in the config.py directory.

Fonctionement
========

Basically the two way to call the script is either on the cli, or by starting the service
if you start the tasks, it will start a celery worker sending the test job to the GenericBox install.
So we have the following project.

    celery_client
        |
        |
        |
        | Rabbitmq broker
        |
        |
        |
        ˅
    celery_server
        |
        |
        |
        | Python call
        |
        |
        |
        ˅
    GenericBox
        |
        |
        |
        | Python call
        |
        |
        |
        ˅
    Vagrant
        |
        |
        |
        | Shell call
        |
        |
        |
        ˅
    VirtualBox
