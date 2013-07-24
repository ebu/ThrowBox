import os
from throw_box import test_box
import unittest

DEFAULT_TEMPLATE = "ubuntu-12.04"

class TestBoxThrower(unittest.TestCase):
    
    def test_box_test(self):
        """
        """
        b = test_box.GenericBox(["echo bou"], [], [], "", DEFAULT_TEMPLATE)
        b.up()
        b.setup()
        test_result = b.test()
        self.assertEqual(test_result, None)
        self.assertEqual(b.output, [["echo bou", "bou"], []])

    def test_invalid_template(self):
        """
        """
        with self.assertRaises(test_box.InvalidTemplate):
            test_box.GenericBox([], [], [], "", "merglkjadsf")


    def test_bad_setup_script(self):
        """
        """
        b = test_box.GenericBox(['true', 'false', 'echo bou'], [], [], "", DEFAULT_TEMPLATE)
        b.up()
        b.setup()
        self.assertEqual(b.output, [['true', 'false']])
        

    def test_test_scripts(self):
        """
        """
        b = test_box.GenericBox([], ["false", "true"], [], "", DEFAULT_TEMPLATE)
        b.up()
        b.test()
        test_result = b.test_results
        self.assertEqual(test_result[0].passed, False)
        self.assertEqual(test_result[1].passed, True)

    def test_clone_repository(self):
        """
        """
        b = test_box.GenericBox([], [], [], "ssh://git@github.com:ebu/ThrowBox.git", DEFAULT_TEMPLATE, private_key="~/.ssh/id_rsa")
        b.clone_repo()
        self.assertIn("README.md", os.listdir(b.directory))

if __name__ == '__main__':
    unittest.main()
