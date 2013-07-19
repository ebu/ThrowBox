from test_box import Box
from celery import Celery
import config

VAGRANT_FILENAME = "Vagrantfile"

celery = Celery('tasks', broker='amqp://guest@localhost//')

@celery.task
def test_job(pre, test, post, template):
    b = Box(pre, test, post, "", template)
    try:
        b.up()
        b.run_pre()
        b.run_test()
    except Exception as e:
        print(e)
    finally:
        b.destroy()
    return b.test_results

@celery.task
def list_box():
    return config.VAGRANT_TEMPLATE_DIR
