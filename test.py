from throw_box import tasks
from throw_box import test_box
import unittest

class TestBoxThrower(unittest.TestCase):
    
    def test_box_test(self):
        b = test_box.GenericBox(["echo bou"], [], [], "", "ubuntu-12.04")
        b.up()
        b.setup()
        test_result = b.test()
        self.assertEqual(test_result, None)
        self.assertEqual(b.output, [["echo bou", "bou"]])
        b.destroy()

    def test_invalid_template(self):
        with self.assertRaises(test_box.InvalidTemplate):
            b = test_box.GenericBox([], [], [], "", "merglkjadsf")


    def test_bad_setup_script(self):
        b = test_box.GenericBox(['true', 'false', 'echo bou'], [], [])
        self.assertEqual(b.output, [['true', 'false']])
        

    def test_test_scripts(self):
        b = test_box.GenericBox([], ["false", "true"], [], "", "ubuntu-12.04")
        b.up()
        test_result = b.test()
        b.destroy()
        self.assertEqual(test_result[0].passed, False)
        self.assertEqual(test_result[1].passed, True)
    
    def test_celery_job(self):
        job = tasks.test_job.delay(["sudo apt-get update", "sudo apt-get install -y git", "sudo apt-get install -y python"], ["false"], [], "ubuntu-12.04", "")
        job.wait()

if __name__ == '__main__':
    unittest.main()
