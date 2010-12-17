#!/usr/bin/python

import os
import sys

os.chdir("/var/www/vhosts/ideoforms.com/apps/pysoso")
os.environ['PYTHON_EGG_CACHE'] = "/var/www/vhosts/ideoforms.com/apps/pysoso/.egg"
sys.path.append("/var/www/vhosts/ideoforms.com/apps/pysoso")

from pysoso import app as application
