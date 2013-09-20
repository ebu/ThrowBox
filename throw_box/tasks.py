from throw_box import test_box
import os
from celery.decorators import task
import logging
from celery import current_task
try:
    from django.conf import settings
except ImportError:
    import config as settings

"""This module is designed to work with django only. you will have issues if you try to use it without
at least setting this settings:
    THROWBOX_PUBKEY_FILE the location of the public key 
    THROWBOX_PRIVKEY_FILE the location of the private key used to clone the repo
    THROWBOX_TEMPLATE_DIR the location of the the vagrant files to use. Their location will 
"""




@task
def list_box():
    """List all the available templates.
    """
    return os.path.lsdir(settings.THROWBOX_PUBKEY_FILE)


@task
def get_pub_key():
    """Return the public key used by the fabric job to clone the repository.
    """
    with open(settings.THROWBOX_PUBKEY_FILE) as f:
        return f.read()


@task
def test_job(setup_scripts, test_scripts, deploy_scripts, github_url, template, repo, build_index):
    """Launch a new test job. It will report a finer state from one of those:
    * INITIALISING: the system is starting
    * CLONING: the repo is being fetched
    * STARTING: the vm is starting.
    * STARTUP FAILED: the vm couldn't be started, this will be used with a StartFailedError Exception
    * SETUPING: the pre script are running one the vm.
    * TESTING: the pre script are running one the vm.
    * DEPLOYING: the post script are running one the vm.
    * DESTROYING: the vm is stopping.
    * FINISHED: the vm is stopped and the job is finished.
    """
    state('INITIALISING')
    if settings.THROWBOX_EC2:
        box = test_box.Ec2Box(setup_scripts, test_scripts, deploy_scripts, github_url, template, template_dir=settings.THROWBOX_TEMPLATE_DIR, private_key=settings.THROWBOX_PRIVKEY_FILE)
    else:
        box = test_box.VirtualBox(setup_scripts, test_scripts, deploy_scripts, github_url, template, template_dir=settings.THROWBOX_TEMPLATE_DIR, private_key=settings.THROWBOX_PRIVKEY_FILE)
    try:
        state('STARTING')
        box.up()

        state('CLONING')
        box.clone_repo()

        commit_sha = box.top_commit_sha
        commit_comment = box.top_commit_comment
        if settings.THROWBOX_EC2:
            box.wait_up()

        state('SETUPING')
        box.setup()

        state('TESTING')
        box.test()
        test_results = box.test_results

        state('DEPLOYING')
        box.deploy()
        outputs = box.output
        logging.info(box.output[0])
        logging.info(type(box.output))
    except Exception as e:
        logging.error(e)
        return
    finally:
        state('DESTROYING')
        del(box)
    state('FINISHED')
    outputs = ["\n".join(o) for o in outputs]
    ret = []
    ret.append(dict(repo=repo, commit_sha=commit_sha, commit_comment=commit_comment, index=build_index, setup_output=outputs[0], test_output=outputs[1], deploy_output=outputs[2]))
    
    for test_result in test_results:
        ret.append(dict(return_code=test_result.exit_code, success=test_result.passed))
    return ret


def state(state, key='job_state'):
    """Report a finer state of the job to the celery caller.
    @param state: the state to set
    """
    current_task.update_state(state=state)
