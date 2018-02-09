"""
Load simulation parameters from each organism species config file.
"""

import configparser
import os, glob

# Find organism filenames
org_files = glob.glob('./*.org')

for org_file in org_files:
	config_org = configparser.ConfigParser()
	config_org.read(org_file)

