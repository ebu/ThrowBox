import os
from throw_box import test_box
from throw_box import tasks
from throw_box import config
import unittest
import re
import boto

DEFAULT_TEMPLATE = "ubuntu-12.04"

class TestBoxThrower(unittest.TestCase):
    
    def test_box_test(self):
        """Test a simple setup script output.
        """
        b = test_box.VirtualBox([("echo bou")], [], [], DEFAULT_TEMPLATE)
        b.up()
        b.setup()
        test_result = b.test()
        self.assertEqual(test_result, None)
        self.assertEqual(b.output, [[("echo bou", "bou")], []])

    def test_invalid_template(self):
        """Test that an invalid template raises an error
        """
        with self.assertRaises(test_box.InvalidTemplate):
            test_box.VirtualBox([], [], [], "merglkjadsf")


    def test_bad_setup_script(self):
        """Test that a bad setup script raises an error
        Also test if the  output stop after the first failing script
        """
        b = test_box.VirtualBox(['true', 'true', 'false', 'echo bou'], [], [], DEFAULT_TEMPLATE)
        b.up()
        with self.assertRaises(test_box.SetupScriptFailed):
            b.setup()
        self.assertEqual(b.output, [[('true', ''), ('true', ''), ('false', '')]])


    def test_test_scripts(self):
        """Test if the test scripts return the correct result, test that the test result are correct
        Test that the return value correspond
        """
        b = test_box.VirtualBox([], ["false", "true", "true"], [], DEFAULT_TEMPLATE)
        b.up()
        b.test()
        b.deploy()
        test_result = b.test_results
        self.assertEqual(test_result[0].passed, False)
        self.assertEqual(test_result[1].passed, True)
        self.assertEqual(test_result[2].passed, True)

    def test_clone_repository(self):
        """Test that a clone repository doesn't fail. Test that the sha of the commit, and the comment are extracted.
        """
        b = test_box.VirtualBox([], [], [], DEFAULT_TEMPLATE)
        b.private_key = "~/.ssh/id_rsa"
        b.git_url =  "git@github.com:ebu/ThrowBox.git"
        b.clone_repo()
        self.assertIn("README.md", os.listdir(os.path.join(b.directory, 'repo')))
        self.assertEqual(len(b.top_commit_sha), 40)
        self.assertRegexpMatches(b.top_commit_comment, re.compile(".+"))


class TestTask(unittest.TestCase):

    @unittest.skipUnless(os.path.exists(config.THROWBOX_PUBKEY_FILE), "no pubkey file found")
    def test_listing_keys(self):
        key = tasks.get_pub_keys()
        self.assertEqual(key, open(config.THROWBOX_PUBKEY_FILE).read())

    def test_listing_template(self):
        templates = test_box.Ec2Box.list_template()
        self.assertGreaterThan(len(templates), 1)
        self.assertMatches(templates[0], re.compile('ami-[0-9a-f]'))
        templates = test_box.VirtualBox.list_template()
        self.assertEqual(templates[0],DEFAULT_TEMPLATE)
        self.assertEqual(len(templates), 1)

    def test_complete_run(self):
        task_result = tasks.test_job([],[],[], "", DEFAULT_TEMPLATE, "", 1)


class TestAmazonBox(unittest.TestCase):
    @unittest.skip
    def test_init(self):
            b = test_box.Ec2Box(["echo bou"], [], [], DEFAULT_TEMPLATE)
            self.assertEqual(len(self.con.get_all_security_groups('throwbox')), 1)
            del b

    @unittest.skip
    def test_test_run(self):
            b = test_box.Ec2Box(["echo bou"], ['true'], [], DEFAULT_TEMPLATE)
            b.up()
            b.wait_up()
            b.setup()
            self.assertEqual(len(b.test_results), 0)
            b.test()
            print(b.test_results)
            self.assertEqual(len(b.test_results), 1)
            self.assertTrue(b.test_results[0].passed)
            del b

    @unittest.skip
    def setUp(self):
        self.con = boto.connect_ec2()
        try:
            self.con.delete_security_group('throwbox')
        except:
            print("no throwbox security group") 

if __name__ == '__main__':
    unittest.main()
