from test_box import GenericBox
import os
from celery import Celery
import config

VAGRANT_FILENAME = "Vagrantfile"

celery = Celery('tasks', broker='amqp://guest@localhost//')

@celery.task
def test_job(pre, test, post, template):
    """Launch a new test job.
    """
    b = GenericBox(pre, test, post, "", template)
    try:
        b.up()
        b.run_pre()
        b.run_tests()
    except Exception as e:
        print(e)
    finally:
        b.destroy()
    return b.test_results

@celery.task
def list_box():
    """List all the available templates.
    """
    return os.path.lsdir(config.VAGRANT_TEMPLATE_DIR)
