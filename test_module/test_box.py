import vagrant
import shutil
from time import sleep
from fabric.api import run, env, task, execute
import tempfile
import os
from config import VAGRANT_TEMPLATE_DIR

TEMPLATES = os.listdir(VAGRANT_TEMPLATE_DIR)

from collections import namedtuple

TestResult = namedtuple("TestResult", ['test', 'exit_code', 'success'])

class Box():
    def __init__(self, pre, tests, post, github_url, template):
        """docstring for __init__"""
        self.pre = pre
        self.post = post
        self.tests = tests
        self.test_results = []
        self.directory = tempfile.mkdtemp()
        os.chdir(self.directory)
        self.set_vagrant_file(template)
        self.v = vagrant.Vagrant()

    def set_vagrant_file(self, template):
        if template not in TEMPLATES:
            print("invalid template")
            exit(1)
        abs_template_file = os.path.join(VAGRANT_TEMPLATE_DIR, template)
        abs_vagrant_file = os.path.join(self.directory, "Vagrantfile")
        shutil.copyfile(abs_template_file, abs_vagrant_file)

    def up(self):
        #self.v.init()
        self.v.up()
        while self.v.status() != 'running':
            print(self.v.status())
            sleep(1)
        env.hosts = [self.v.user_hostname_port()]
        env.key_filename = self.v.keyfile()

    def run_test(self):
        @task 
        def test_runner(test):
                result = run(test, warn_only=True)
                print dir(result)
                return TestResult(test, result.return_code, result.succeeded)

        @task
        def run_test(tests):
            for test in tests:
                result = test_runner(test)
                self.test_results.append(result)

        execute(run_test, self.tests)
        print self.test_results

    def run_pre(self):
        @task
        def run_pre(commands):
            for command in commands:
                print(run(command))
        execute(run_pre, self.pre)

    def destroy(self):
        try:
            self.v.destroy()
        except:
            #pretty bad thing just append
            os.unlink("Vagrantfile")
