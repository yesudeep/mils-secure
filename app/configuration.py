#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Application configuration.
# Copyright (c) 2009 happychickoo.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Notes:
# ======
# Two additional services for static content delivery are used.
#
#  1. Dropbox for binary media content.
#  2. Our own server that uses nginx for text-based content delivery.
#
# Why use another static server when Dropbox works?
# -------------------------------------------------
# Dropbox delivers binary media content just fine, but does not compress
# them before delivery.  We want at least the JS files to be compressed
# before delivery. CSS is served by Dropbox because it reference images
# using relative paths which ends up hitting our hosted static server.
#
# Why not use App Engine to serve static files?
# ---------------------------------------------
# App Engine does not send a "304 not modified" HTTP status for
# static files and hence these files do not get cached by the browser.
# And serving static files without caching results in a slow Website.
#
# Why use App Engine to serve static files?
# -----------------------------------------
#
#    1. Google CDN.
#    2. Browser based cache works (partially)
#
#  Disadvantages:
#
#    1. Does not send a 304 Not modified header.
#    2. Every domain has a limit on the number of connections.
#       Separating media into a subdomain lets the browser
#       open more connections and download more media simultaneously.

import sys
import os

from os.path import dirname, abspath, realpath, join as path_join

DIR_PATH = abspath(dirname(realpath(__file__)))
EXTRA_LIB_PATH = [
    path_join(DIR_PATH, 'appengine'),
    path_join(DIR_PATH, 'jinja2'),
    path_join(DIR_PATH, 'gaeutilities'),
    dirname(DIR_PATH),
]
sys.path = EXTRA_LIB_PATH + sys.path

def sanitize_url(url):
    """
    Ensures the url ends with a slash.
    """
    if not url.endswith('/'):
        url = url + '/'
    return url

# Static data.
NAKED_DOMAIN = 'milsalumni.org'
MAIL_SENDER = 'no-reply@%s' % NAKED_DOMAIN
ADMIN_MAIL_SENDER = 'administrator@%s' % NAKED_DOMAIN
ADMIN_EMAIL = ADMIN_MAIL_SENDER
CONTACT_EMAIL = 'hello@%s' % NAKED_DOMAIN
MODE_DEVELOPMENT = 'development'
MODE_PRODUCTION = 'production'

APPLICATION_ID = os.environ['APPLICATION_ID']
APPLICATION_TITLE = 'MILS Alumni'
SERVER_PORT = os.environ['SERVER_PORT']
SERVER_NAME = os.environ['SERVER_NAME']
SERVER_SOFTWARE = os.environ['SERVER_SOFTWARE']

if SERVER_PORT and SERVER_PORT != '80':
    # Development mode.
    DEPLOYMENT_MODE = MODE_DEVELOPMENT
    HOST_NAME = '%s:%s' % (SERVER_NAME, SERVER_PORT)
    LOCAL = True
    DEBUG = True
    MEDIA_URL = 'http://%s/s/' % (HOST_NAME, )
    TEXT_MEDIA_URL = MEDIA_URL
else:
    # Production mode.
    DEPLOYMENT_MODE = MODE_PRODUCTION
    HOST_NAME = SERVER_NAME
    LOCAL = False
    DEBUG = False
    #MEDIA_URL = "http://static.%s/u/3035045/public/" % NAKED_DOMAIN
    TEXT_MEDIA_URL = "http://assets.%s/" % NAKED_DOMAIN
    MEDIA_URL = TEXT_MEDIA_URL
    #MEDIA_URL = 'http://%s/s/' % (HOST_NAME, )
    #TEXT_MEDIA_URL = MEDIA_URL

if DEBUG:
    # Minification suffixes for use with CSS and JS files.
    CSS_MINIFIED = '-min'
    JS_MINIFIED = '-min'
else:
    CSS_MINIFIED = '-min'
    JS_MINIFIED = '-min'

ROOT_URL = 'http://%s/' % (HOST_NAME, )

# rpxnow.com
RPX_NOW_TOKEN_URL = 'http://%s/account/rpx' % (HOST_NAME, )
RPX_NOW_REALM = 'mils-alumni-secure'
RPX_NOW_DOMAIN = '%s.rpxnow.com' % RPX_NOW_REALM
RPX_NOW_API_AUTH_URL = 'https://rpxnow.com/api/v2/auth_info'
RPX_NOW_LANGUAGE = 'en'

# Other information
BOOK_VENDOR_EMAIL = 'varsha@embassybooks.in'
BOOK_VENDOR_PHONE_NUMBER = '9819001820'
BOOK_VENDOR_NAME = 'Varsha Shah'
SUBJECT_PREFIX = "[MILS Alumni]"
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
Name : MILS Alumni Association
Bank   : Indian Overseas Bank
Branch : New Marine Lines
CDCC A/c. No. : 7360
IFSC : IOBA0000301.
'''
PICASA_WEB_ALBUMS_PUBLIC_URL = 'http://picasaweb.google.com/mils.secure'
GOOGLE_ANALYTICS_ID = "UA-7340598-3"

# ---------------------------------------------------------------------------
# Stuff that should be different in production.
cdn_urls = {
    'microsoft.jquery-1.3.2': "http://ajax.microsoft.com/ajax/jQuery/jquery-1.3.2.min.js",
    'google.jquery-1.3.2': "http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js",
    'jquery.jquery-1.4': "http://code.jquery.com/jquery-1.4a1.min.js",
    'local.jquery-1.4': "%sscript/lib/chickoojs/src/jquery/jquery-1.4a1.min.js" % (MEDIA_URL,),
    'local.jquery-1.3.2': "%sscript/lib/chickoojs/src/jquery/jquery-1.3.2.min.js" % (MEDIA_URL,),
    'assets.jquery-1.4': "http://assets.%s/script/lib/chickoojs/src/jquery/jquery-1.4a1.min.js" % (NAKED_DOMAIN, ),
}

if LOCAL:
    JQUERY_URL = cdn_urls.get('local.jquery-1.4')
    ANALYTICS_CODE = ""
else:
    JQUERY_URL = cdn_urls.get('assets.jquery-1.4')
    ANALYTICS_CODE = """
<script type="text/javascript">
var _gaq = _gaq || [];
_gaq.push(['_setAccount', '%(GOOGLE_ANALYTICS_ID)s']);
_gaq.push(['_trackPageview']);
(function() {
  var doc=document, ga = doc.createElement('script');
  ga.src = ('https:' == doc.location.protocol ? 'https://ssl' :
      'http://www') + '.google-analytics.com/ga.js';
  ga.setAttribute('async', 'true');
  doc.documentElement.firstChild.appendChild(ga);
})();
</script>
""" % dict(GOOGLE_ANALYTICS_ID=GOOGLE_ANALYTICS_ID)


TEMPLATE_BUILTINS = {
    'ADMIN_MAIL_SIGNATURE': ADMIN_MAIL_SIGNATURE,
    'CSS_MINIFIED': CSS_MINIFIED,
    'GOOGLE_ANALYTICS_ID': GOOGLE_ANALYTICS_ID,
    'JS_MINIFIED': JS_MINIFIED,
    'LOCAL': LOCAL,
    'MAIL_SIGNATURE': MAIL_SIGNATURE,
    'MEDIA_URL': sanitize_url(MEDIA_URL),
    'MINIFIED': JS_MINIFIED,
    'PICASA_WEB_ALBUMS_PUBLIC_URL': PICASA_WEB_ALBUMS_PUBLIC_URL,
    'RPX_NOW_DOMAIN': RPX_NOW_DOMAIN,
    'RPX_NOW_LANGUAGE': RPX_NOW_LANGUAGE,
    'RPX_NOW_REALM': RPX_NOW_REALM,
    'RPX_NOW_TOKEN_URL': RPX_NOW_TOKEN_URL,
    'TEMPLATE_DEBUG': DEBUG,
    'TEXT_MEDIA_URL': sanitize_url(TEXT_MEDIA_URL),
    'ANALYTICS_CODE': ANALYTICS_CODE,
    'JQUERY_URL': JQUERY_URL,
}

TEMPLATE_DIRS = [
    path_join(DIR_PATH, 'templates'),
]
