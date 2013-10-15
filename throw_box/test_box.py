import logging
import hashlib
from multiprocessing import Lock
from paramiko.ssh_exception import SSHException
import shutil
from time import sleep
from fabric.api import run, env, task, execute, local, lcd, put
import tempfile
import os
import vagrant
import boto
import time
from throw_box import config

from collections import namedtuple

class InvalidTemplate(ValueError):
    """Error throwned when a template that doesn't exist
    was specified
    """
    pass


class SetupScriptFailed(Exception):
    """Error throwned when the setup script failed
    """
    pass


class StartFailedError(Exception):
    """Error throwned when the startup of the machine failed
    """
    pass


"""Tuple that host the result of a single test run.
"""
TestResult = namedtuple("TestResult", ['test', 'exit_code', 'passed'])

REPO_ROOT = "repo"

MAX_RETRY_STATUS = 300

class GenericBox(object):
    """This class is a abstract box. It handles:
    * The initialisation of the box
    * The run of the scripts in the vm.
    * The teardown of the vm used to run the script.
    """
    def setup_git_url(self, git_url):
        self.git_url = git_url

    def __init__(self, setup_scripts, test_scripts, deploy_scripts, template):
        """Construct a new box definition. 
        All the scripts are list of string, each entry being
        a shell command sh compatible.
        @param setup_scripts: A list of script to run before the test scripts are run. Those
                    must be shell script, one line per element of the list. cf. run_tests
        @param test_scripts: A list of script to run. They act as the test of the softwar
        @param deploy_scripts: A list of script to run after the build is complete. This can be used to
                     distribute or package the software.
        @param git_url: The github url of the tested repo. This will be cloned at the beginning 
                           of the script
        @param template: A string matching the template you wanna use cf. set_vagrant_env.
        @param template_dir: The directory in which the vagrant templates are stored.
        @param private_key: the private key used to clone the repo
        """
        self.setup_scripts = setup_scripts
        self.test_scripts = test_scripts
        self.deploy_scripts = deploy_scripts
        self.test_results = []
        self.output = []
        self.directory = tempfile.mkdtemp()
        self.vagrant_slave = vagrant.Vagrant(self.directory)
        self.template = template


    @property
    def top_commit_sha(self):
        """Return the sha of the commit
        """
        with lcd(self.directory):
            with lcd(REPO_ROOT):
                return local("git rev-list -n 1 HEAD", capture=True).strip()
    @property
    def top_commit_comment(self):
        with lcd(self.directory):
            with  lcd(REPO_ROOT):
                return local("git log -n 1 HEAD --pretty=%s", capture=True).strip()

    def clone_repo(self):
        """clone the repository given by self.git_url at the vagrant root, it will be in /vagrant
        """
        with lcd(self.directory):
            local("git clone {} {}".format(self.git_url, REPO_ROOT))

    def up(self):
        """Start the vagrant box.
        """
        try:
            self.vagrant_slave.up()
            self.wait_up()
            env.hosts = [self.vagrant_slave.user_hostname_port()]
            env.key_filename = self.vagrant_slave.keyfile()
        except:
            raise StartFailedError()


    def wait_up(self):
        """wait for the vm to be up, and the ssh to be accessible
        """
        for _ in range(MAX_RETRY_STATUS):
            if self.vagrant_slave.status() != 'starting':
                break
            sleep(1)
        else:
            raise StartFailedError()
        env.host_string = self.vagrant_slave.user_hostname_port()
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
            return TestResult(test, int(result.return_code), bool(result.succeeded))

        @task
        def run_tests(tests):
            """Run all the tests, append the result of 
            the test in self.test_results
            @param tests: A list of string representing the sh command
            """
            for test in tests:
                result = test_runner(test)
                self.test_results.append(result)
        self.output.append([])
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
                ret = self.run(command, warn_only=True)
                if ret.failed:
                    raise SetupScriptFailed()
        self.output.append([])
        execute(run_pre, self.setup_scripts)
        return True

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
        self.output.append([])
        run_post(self.deploy_scripts)

    def run(self, command, *args, **kwargs):
        """a run wrapper that append the output of the command 
        and the command to the self.output list
        @param command:
        """
        try:
            ret = run(command.strip(), *args, **kwargs)
        except SSHException:
            raise
        out = ret.stdout.replace('\r\r', '\n')
        out = ret.stdout.replace('\r\n', '\n')
        out = ret.stdout.replace('\r', '\n')
        self.output[-1].append((command, out, ))
        return ret

    def __del__(self):
        """Destroy the box"""
        try:
            self.vagrant_slave.destroy()
        except AttributeError:
            #if we have a vagrant box setup
            pass
        except Exception as e:
            #pretty bad thing just append
            logging.error("Issue while destroying the box, {!s}".format(e))
        finally:
            #remove the directory at any price
            shutil.rmtree(self.directory)

    @staticmethod
    def list_template(self):
        return []

class VirtualBox(GenericBox):
    """VirtualBox Box, simply lock the startup of the box"""
    l = Lock()
    def __init__(self, *args, **kwargs):
        super(VirtualBox, self).__init__(*args, **kwargs)
        self.vagrant_template_dir = config.THROWBOX_TEMPLATE_DIR
        self.set_vagrant_env()

    @staticmethod
    def list_template(self, dir_path=None):
        return os.path.lsdir(dir_path or config.THROWBOX_TEMPLATE_DIR)

    def up(self):
        """Start the vagrant box.
        """
        with VirtualBox.l:
            self.vagrant_slave.up()
        self.wait_up()
        env.host_string = self.vagrant_slave.user_hostname_port()
        env.key_filename = self.vagrant_slave.keyfile()

    def set_vagrant_env(self):
        """Set the vagrant file
        @param vagrant_template: A string matching the name of the vagrant template to use
        """
        templates = os.listdir(self.vagrant_template_dir)
        if self.template not in templates:
            raise InvalidTemplate("Template '{!s}' cannot be found".format(self.template))
        abs_template_file = os.path.join(self.vagrant_template_dir, self.template)
        abs_vagrant_file = os.path.join(self.directory, "Vagrantfile")
        shutil.copyfile(abs_template_file, abs_vagrant_file)

class Ec2Box(GenericBox):
    """Interface to an ec2 box
    """

    l = Lock()
    def __init__(self, *args, **kwargs):
        super(Ec2Box, self).__init__(*args, **kwargs)
        self.con = boto.connect_ec2()
        self.key_pair = self.con.create_key_pair('throwbox' + hashlib.md5(self.directory).hexdigest())
        self.key_dir = os.path.join(self.directory, "key")
        os.mkdir(self.key_dir)
        self.key_pair.save(self.key_dir)
        priv_key_file = filter(lambda a: a.endswith("pem"), os.listdir(self.key_dir))[0]
        self.priv_key_file = os.path.join(self.key_dir, priv_key_file)

        self.instance = None
        self.template = "ami-53b1ff3a"

    @staticmethod
    def list_template(self):
        con = boto.connect_ec2()
        return [i.name for i in con.get_all_images()]

    def ensure_security_group(self):
        with Ec2Box.l:
            #check if the security group throwbox is there, else we create it
            try:
                security_groups = self.con.get_all_security_groups("throwbox")
            except:
                self.security_group = self.con.create_security_group('throwbox', 'throwbox configuration')
                self.security_group.authorize('tcp', 22, 22, "0.0.0.0/0")
            else:
                self.security_group = security_groups[0]


    def up(self):
        """Start an ec2 instance"""
        reservation = self.con.run_instances(self.template, instance_type="t1.micro", security_groups=[self.security_group.name], key_name=self.key_pair.name)
        self.instance = reservation.instances[0]

    @property
    def __instance_id(self):
        self.instance.id

    def __del__(self):
        if self.instance:
            self.instance.terminate()
        if self.key_pair:
            self.key_pair.delete()
        shutil.rmtree(self.directory)

    def wait_up(self):
        """wait for the ec2 instance to be up"""
        while self.instance.state != 'running':
            time.sleep(5)
            self.instance.update()
        time.sleep(30)
        env.key_filename = self.priv_key_file
        env.hosts = [self.instance.ip_address]
        env.user = "ubuntu"
        env.host_string = env.user + "@" + self.instance.ip_address
        print env.host_string

    def clone_repo(self):
        super(Ec2Box, self).clone_repo()
        repo_path = os.path.join(self.directory, REPO_ROOT)
        put(repo_path, '.')
