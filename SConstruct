#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from util import get_project_config
from colorizer import colorizer

col = colorizer()

env = Environment(tools=['default', 'puppy_tools'])
col.colorize(env)

Export('env')

puppy_config = get_project_config(os.getcwd())

env['APP_DIR'] = puppy_config.query('application.app_dir', 'app')
env['TEMPLATES_DEST_DIR'] = puppy_config.query('build.templates.dest_dir', 'app/templates')
env['MEDIA_SRC_DIR'] = puppy_config.query('build.media.src_dir', 'media')
env['MEDIA_DEST_DIR'] = puppy_config.query('build.media.dest_dir', 'app/public')

SConscript([
    'media/SConscript',
    'templates/SConscript',
])

