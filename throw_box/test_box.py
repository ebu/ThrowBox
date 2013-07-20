import logging
import shutil
from time import sleep
from fabric.api import run, env, task, execute
import tempfile
import os
import vagrant
import config

from collections import namedtuple

"""Tuple that host the result of a single test run.
"""
TestResult = namedtuple("TestResult", ['test', 'exit_code', 'success'])

class GenericBox(object):
    """This class is a abstract box. It handles:
    * The initialisation of the box
    * The run of the scripts in the vm.
    * The teardown of the vm used to run the script.
    """
    def __init__(self, setup_scripts, test_scripts, deploy_scripts, github_url, template):
        """Construct a new box definition. This method will only create a new
        vagrant environment. All the scripts are list of string, each entry being
        a shell command sh compatible.
        @param pre: A list of script to run before the test scripts are run. Those
                    must be shell script, one line per element of the list. cf. run_tests
        @param tests: A list of script to run. They act as the test of the softwar
        @param post: A list of script to run after the build is complete. This can be used to
                     distribute or package the software.
        @param github_url: The github url of the tested repo. This will be cloned at the beginning 
                           of the script
        @param template: A string matching the template you wanna use cf. set_vagrant_env.
        """
        self.setup_scripts = setup_scripts
        self.test_scripts = test_scripts
        self.deploy_scripts = deploy_scripts
        self.test_results = []
        self.directory = tempfile.mkdtemp()
        self.set_vagrant_env(template)
        self.vagrant_slave = vagrant.Vagrant()
        self.output = []

    def set_vagrant_env(self, vagrant_template):
        """Set the vagrant file
        @param vagrant_template: A string matching the name of the vagrant template to use
        """
        templates = os.listdir(config.VAGRANT_TEMPLATE_DIR)
        if vagrant_template not in templates:
            print("invalid template")
            exit(1)
        abs_template_file = os.path.join(config.VAGRANT_TEMPLATE_DIR, vagrant_template)
        abs_vagrant_file = os.path.join(self.directory, "Vagrantfile")
        shutil.copyfile(abs_template_file, abs_vagrant_file)
        os.chdir(self.directory)

    def up(self):
        """Start the vagrant box.
        """
        self.vagrant_slave.up()
        while self.vagrant_slave.status() != 'running':
            print(self.vagrant_slave.status())
            sleep(1)
        env.hosts = [self.vagrant_slave.user_hostname_port()]
        env.key_filename = self.vagrant_slave.keyfile()

    def test(self):
        """Run each line of self.tests.
        """
        @task 
        def test_runner(test):
            """run a singleTest, return the result.
            @param test: A string representing the sh command.
            @return :A TestResult namedtuple. cf. TestResult
            """
            result = self.run(test, warn_only=True)
            return TestResult(test, result.return_code, result.succeeded)

        @task
        def run_tests(tests):
            """Run all the tests, append the result of 
            the test in self.test_results
            @param tests: A list of string representing the sh command
            """
            for test in tests:
                result = test_runner(test)
                self.test_results.append(result)

        execute(run_tests, self.test_scripts)

    def setup(self):
        """Run the setup scripts, abort if any error occurs
        """
        @task
        def run_pre(commands):
            """Run a list of commands, stop if any of them fail.
            @param commands: A list of string 
            """
            for command in commands:
                self.run(command)
        execute(run_pre, self.setup_scripts)

    def deploy(self):
        """Run the post test scripts, continue on error
        """
        @task
        def run_post(commands):
            """Run a list of commands, continue if any of them fail
            @param commands: A list of string 
            """
            for command in commands:
                self.run(command, warn_only=True)

    def run(self, *args, **kwargs):
        """a run wrapper that append the output of the command 
        and the command to the self.output list
        @param command:
        """
        return run(*args, **kwargs)

    def destroy(self):
        """Destroy the box
        """
        try:
            self.vagrant_slave.destroy()
        except Exception as e:
            #pretty bad thing just append
            logging.error("Issue while destroying the box, {!s}".format(e))
        finally:
            #remove the directory at any price
            os.chdir("..")
            shutil.rmtree(self.directory)
