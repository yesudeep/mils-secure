#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from os.path import dirname, abspath, realpath, join as path_join

DIR_PATH = abspath(dirname(realpath(__file__)))
EXTRA_LIB_PATH = [
    path_join(DIR_PATH, 'lib'),
    path_join(DIR_PATH, 'lib', 'libs.zip'),
    dirname(DIR_PATH),
]
sys.path = EXTRA_LIB_PATH + sys.path
logging.basicConfig(level=logging.INFO)

# Static data.
MAIL_SENDER = 'no-reply@milsalumni.org'
ADMIN_MAIL_SENDER = 'administrator@milsalumni.org'
ADMIN_EMAIL = 'administrator@milsalumni.org'
CONTACT_EMAIL = 'hello@milsalumni.org'

BOOK_VENDOR_EMAIL = 'varsha@embassybooks.in'
BOOK_VENDOR_PHONE_NUMBER = '9819001820'
BOOK_VENDOR_NAME = 'Varsha Shah'

MAIL_SIGNATURE = '''--
Cheers,
Administrator
www.milsalumni.org
--
Please do not reply to this system generated message.
'''

ADMIN_MAIL_SIGNATURE = '''--
Cheers,
Website Administrator, MILS Alumni Association
'''

PAYMENT_DETAILS = '''
Payment details go here.
'''

PICASA_WEB_ALBUMS_PUBLIC_URL = 'http://picasaweb.google.com/mils.secure'


def sanitize_url(url):
    """
    Ensures the url ends with a slash.
    """
    if not url.endswith('/'):
        url = url + '/'
    return url

MODE_DEVELOPMENT = 'development'
MODE_PRODUCTION = 'production'

APPLICATION_ID = os.environ['APPLICATION_ID']
SERVER_PORT = os.environ['SERVER_PORT']
SERVER_NAME = os.environ['SERVER_NAME']
SERVER_SOFTWARE = os.environ['SERVER_SOFTWARE']
if SERVER_PORT and SERVER_PORT != '80':
    # Development mode.
    DEPLOYMENT_MODE = MODE_DEVELOPMENT
    HOST_NAME = '%s:%s' % (SERVER_NAME, SERVER_PORT)
    LOCAL = True
    DEBUG = True
    SECURE_URL = '/'
    #MINIFIED = '-min'
    MINIFIED = ''
else:
    # Production mode.
    DEPLOYMENT_MODE = MODE_PRODUCTION
    HOST_NAME = SERVER_NAME
    LOCAL = False
    DEBUG = False
    SECURE_URL = 'https://%s.appspot.com/' % APPLICATION_ID
    MINIFIED = '-min'

ABSOLUTE_ROOT_URL = 'http://%s/' % (HOST_NAME, )
PRIMARY_URL = ABSOLUTE_ROOT_URL
MEDIA_URL = PRIMARY_URL + 's/'

# rpxnow.com
RPX_NOW_TOKEN_URL = 'http://%s/account/rpx' % (HOST_NAME, )
RPX_NOW_REALM = 'mils-alumni-secure'
RPX_NOW_DOMAIN = '%s.rpxnow.com' % RPX_NOW_REALM
#RPX_NOW_POPUP_HTML = '''
#<a class="rpxnow" onclick="return false;"
#   href="https://%(realm)s.rpxnow.com/openid/v2/signin?token_url=%(token_url)s">
#  Login
#</a>''' % dict(realm=RPX_NOW_REALM, token_url=RPX_NOW_TOKEN_URL)
#RPX_NOW_INLINE_HTML = ''''''
RPX_NOW_API_AUTH_URL = 'https://rpxnow.com/api/v2/auth_info'
RPX_NOW_LANGUAGE = 'en'

TEMPLATE_BUILTINS = {
    'MEDIA_URL': sanitize_url(MEDIA_URL),
    'PRIMARY_URL': sanitize_url(PRIMARY_URL),
    'ABSOLUTE_ROOT_URL': sanitize_url(ABSOLUTE_ROOT_URL),
    'SECURE_URL': sanitize_url(SECURE_URL),
    'TEMPLATE_DEBUG': DEBUG,
    'RPX_NOW_REALM': RPX_NOW_REALM,
    'RPX_NOW_DOMAIN': RPX_NOW_DOMAIN,
    'RPX_NOW_TOKEN_URL': RPX_NOW_TOKEN_URL,
    #'RPX_NOW_POPUP_HTML': RPX_NOW_POPUP_HTML,
    #'RPX_NOW_INLINE_HTML': RPX_NOW_INLINE_HTML,
    'RPX_NOW_LANGUAGE': RPX_NOW_LANGUAGE,
    'PICASA_WEB_ALBUMS_PUBLIC_URL': PICASA_WEB_ALBUMS_PUBLIC_URL,
    'ADMIN_MAIL_SIGNATURE': ADMIN_MAIL_SIGNATURE,
    'MAIL_SIGNATURE': MAIL_SIGNATURE,
    'MINIFIED': MINIFIED,
    'LOCAL': LOCAL,
}

TEMPLATE_DIRS = [
    path_join(DIR_PATH, 'templates'),
]
