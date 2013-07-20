"""The directory hosting all the vagrant files
Their names are used as template name. cf. GenericBoxes """
VAGRANT_TEMPLATE_DIR = '/tmp/vagrant'

"""The maximum number of retry to connect to the vm 
trough ssh when the machine is up
""" 
MAX_RETRY_SSH = 200
"""Time to wait between two retry of ssh connection """
RETRY_SSH_TIME = 1

"""The maximum number of retry between two status check
for the vm to be up """
MAX_RETRY_STATUS = 400
"""Time to wait between two status check for the vm to 
be up
"""
RETRY_STATUS_TIME = 1
