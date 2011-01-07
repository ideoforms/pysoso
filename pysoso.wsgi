#!/usr/bin/python

import os
import sys

ROOT = "/var/www/vhosts/ideoforms.com/apps/pysoso"

os.chdir(ROOT)
os.environ['PYTHON_EGG_CACHE'] = os.path.join(ROOT, ".egg")
sys.path.append(ROOT)

from pysoso import app as application
