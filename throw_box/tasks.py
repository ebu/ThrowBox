from test_box import GenericBox
import os
from celery import Celery, current_task, ResultSet
import config

VAGRANT_FILENAME = "Vagrantfile"

celery = Celery('tasks') 

@celery.task
def test_job(pre, test, post, template, github_url):
    """Launch a new test job. It will report a finer state from one of those:
    * STARTING: the vm is starting
    * SETUPING: the pre script are running one the vm
    * TESTING: the pre script are running one the vm
    * DEPLOYING: the post script are running one the vm
    * DESTROYING: the vm is stopping.
    * DESTROYING: the vm is stopping.
    * FINISHED: the vm is stopped and the job is finished
    """
    state('STARTING')
    b = GenericBox(pre, test, post, github_url, template)
    try:
        state('SETUPING')
        b.setup()
        state('TESTING')
        b.test()
        state('DEPLOYING')
        b.deploy()
    except Exception as e:
        print(e)
    finally:
        result = (b.test_results, b.output)
        state('DESTROYING')
        del(b)
    state('FINISHED')
    return result

def state(state, key='job_state'):
    """Report a finer state of the job to the celery caller.
    @param state: the state to set
    """
    current_task.update_state(meta={key: state})

@celery.task
def list_box():
    """List all the available templates.
    """
    return os.path.lsdir(config.VAGRANT_TEMPLATE_DIR)
