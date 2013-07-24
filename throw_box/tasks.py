from test_box import VirtualBox
import os
from celery import Celery, current_task
from django.conf import settings

"""This is the default FILENAME used by vagrant """
VAGRANT_FILENAME = "Vagrantfile"

"""the celery worker """
celery = Celery('tasks') 

@celery.task
def test_job(setup_scripts, test_scripts, deploy_scripts, github_url, template):
    """Launch a new test job. It will report a finer state from one of those:
    * STARTING: the vm is starting.
    * SETUPING: the pre script are running one the vm.
    * TESTING: the pre script are running one the vm.
    * DEPLOYING: the post script are running one the vm.
    * DESTROYING: the vm is stopping.
    * DESTROYING: the vm is stopping.
    * FINISHED: the vm is stopped and the job is finished.
    """
    state('STARTING')
    box = VirtualBox(setup_scripts, test_scripts, deploy_scripts, github_url, template, template_root=settings.VAGRANT_TEMPLATE_DIR)
    try:
        if github_url:
            box.clone_repo()
        box.up()
        state('SETUPING')
        box.setup()
        state('TESTING')
        box.test()
        state('DEPLOYING')
        box.deploy()
    except Exception as e:
        print(e)
    finally:
        result = {'result':box.test_results,'output':box.output}
        state('DESTROYING')
        del(box)
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
    return os.path.lsdir(settings.VAGRANT_TEMPLATE_DIR)

@celery.task
def get_pub_key():
    """Return the public key used by the fabric job to clone the repository.
    """
    with open(settings.THROWBOX_PUBKEY_FILE) as f:
        return f.read()
