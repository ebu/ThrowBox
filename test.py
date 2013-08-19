import os
from throw_box import test_box
import unittest

DEFAULT_TEMPLATE = "ubuntu-12.04"

class TestBoxThrower(unittest.TestCase):
    
    def test_box_test(self):
        """Test a simple setup output
        """
        b = test_box.VirtualBox(["echo bou"], [], [], "", DEFAULT_TEMPLATE)
        b.up()
        b.setup()
        test_result = b.test()
        self.assertEqual(test_result, None)
        self.assertEqual(b.output, [["echo bou", "bou"], []])

    def test_invalid_template(self):
        """Test that an invalid template raises an error
        """
        with self.assertRaises(test_box.InvalidTemplate):
            test_box.VirtualBox([], [], [], "", "merglkjadsf")


    def test_bad_setup_script(self):
        """Test that a bad setup script raises an error
        Also test if the  output correspond
        """
        b = test_box.VirtualBox(['true', 'true', 'false', 'echo bou'], [], [], "", DEFAULT_TEMPLATE)
        b.up()
        with self.assertRaises(test_box.SetupScriptFailed):
            b.setup()
        self.assertEqual(b.output, [['true', '', 'true', '', 'false', '']])


    def test_test_scripts(self):
        """
        """
        b = test_box.VirtualBox([], ["false", "true", "true"], [], "", DEFAULT_TEMPLATE)
        b.up()
        b.test()
        b.deploy()
        test_result = b.test_results
        self.assertEqual(test_result[0].passed, False)
        self.assertEqual(test_result[1].passed, True)

    def test_clone_repository(self):
        """
        """
        b = test_box.VirtualBox([], [], [], "git@github.com:ebu/ThrowBox.git", DEFAULT_TEMPLATE, private_key="~/.ssh/id_rsa")
        b.clone_repo()
        self.assertIn("README.md", os.listdir(os.path.join(b.directory, 'repo')))
        self.assertEqual(len(b.top_commit_sha), 40)

if __name__ == '__main__':
    unittest.main()
