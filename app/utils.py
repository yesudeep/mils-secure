
import configuration as config
from jinja2 import Environment, FileSystemLoader
from functools import partial
from google.appengine.ext import webapp
from google.appengine.api import users, memcache
import models
from google.appengine.api.labs import taskqueue
from appengine_utilities.sessions import Session
import re
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    mynewdata
except NameError:
    logging.error("damn")
    mynewdata = {}
import base64
def get_data_by_name(name):
    if base64.b64encode(name) in mynewdata:
        return mynewdata[base64.b64encode(name)]
    return None
class PythonLoader(FileSystemLoader):
    """A Jinja2 loader that loads pre-compiled templates."""
    def load(self, environment, name, globals=None):
        """Loads a Python code template."""
        if globals is None:
            globals = {}
        #try for a variable cache
        code = get_data_by_name(name)
        if code is not None:
            logging.info("ultrafast memcache")
        else:
            logging.info("slow memcache")
            code = memcache.get(name)
            if code is None:
                logging.info("oops no memcache!!")
                source, filename, uptodate = self.get_source(environment, name)
                template = file(filename).read().decode('ascii').decode('utf-8')
                code = environment.compile(template, raw=True)
                memcache.set(name,code)
                logging.info(name)
            else:
                logging.info("yeh memcache")
            code = compile(code, name, 'exec')
            mynewdata[base64.b64encode(name)] = code
        return environment.template_class.from_code(environment, code,globals)

#Jinja2 custom filters
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

jinja_env = Environment(loader=PythonLoader(['templates']))
jinja_env.filters['datetimeformat'] = datetimeformat


STATIC_PAGE_CACHE_TIMEOUT = 15   # half an hour.

dec = partial(int, base=10)

def birthdate_to_tuple(birthdate):
    birthdate_year, birthdate_month, birthdate_day = birthdate.split('-')
    if birthdate_year == '0000':
         birthdate_year = str(models.DEFAULT_BIRTHDATE[0])
    return (dec(birthdate_year), dec(birthdate_month), dec(birthdate_day))

def birthdate_to_string(*birthdate_items):
    return '%d-%d-%d' % birthdate_items

def parse_iso_datetime_string(datetime_string):
    if 'T' in datetime_string:
        date_string, time_string = datetime_string.split('T')
    else:
        date_string = datetime_string
        time_string = '00:00:00'
    year, month, day = date_string.split('-')
    hours, minutes, seconds = time_string.split(':')
    year = dec(year)
    month = dec(month)
    day = dec(day)
    hours = dec(hours)
    minutes = dec(minutes)
    seconds = dec(seconds)
    return datetime(year, month, day, hours, minutes, seconds)



def queue_task(queue_name='default', *args, **kwargs):
    #taskqueue.Task(*args, **kwargs).add(queue_name=queue_name)
    taskqueue.Task(*args, **kwargs).add(queue_name)
    info = ' %(url)s %(method)s' % kwargs
    logging.info('[%s]' % (queue_name,) + info)

def queue_mail_task(*args, **kwargs):
    queue_task(queue_name='mail-queue', *args, **kwargs)

class SessionUser(object):
    def __init__(self, **kwargs):
        self.dictionary = kwargs
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def to_dict(self):
        return self.dictionary

class SessionRequestHandler(webapp.RequestHandler):
    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.session = Session()
        if not 'is_logged_in' in self.session:
            self.session['is_logged_in'] = False

    def get_session_user(self):
        if self.is_logged_in():
            session_user = SessionUser(
                identifier = self.session.get('identifier', ''),
                username = self.session.get('username', ''),
                nickname = self.session.get('nickname', ''),
                email = self.session.get('email', ''),
                verified_email = self.session.get('verified_email', ''),
                auth_provider = self.session.get('auth_provider', ''),
                profile_url = self.session.get('profile_url', ''),
                formatted_name = self.session.get('formatted_name', ''),
                first_name = self.session.get('first_name', ''),
                last_name = self.session.get('last_name', ''),
                middle_name = self.session.get('middle_name', ''),
                prefix = self.session.get('prefix', ''),
                suffix = self.session.get('suffix', ''),

                gender = self.session.get('gender', ''),
                phone_number = self.session.get('phone_number', ''),
                photo = self.session.get('photo', ''),

                birthdate = self.session.get('birthdate', models.DEFAULT_BIRTHDATE_STRING),
                birthdate_year = self.session.get('birthdate_year', models.DEFAULT_BIRTHDATE[0]),
                birthdate_month = self.session.get('birthdate_month', models.DEFAULT_BIRTHDATE[1]),
                birthdate_day = self.session.get('birthdate_day', models.DEFAULT_BIRTHDATE[2]),

                address_formatted = self.session.get('address_formatted', ''),
                address_state_province = self.session.get('address_state_province', ''),
                address_street_name = self.session.get('address_street_name', ''),
                address_locality = self.session.get('address_locality', ''),
                address_zip_code = self.session.get('address_zip_code', ''),
                address_country = self.session.get('address_country', '')
                )
            return session_user
        else:
            return None

    def log_in(self, session_user):
        self.session['identifier'] = session_user.identifier
        self.session['username'] = session_user.username
        self.session['nickname'] = session_user.nickname
        self.session['verified_email'] = session_user.verified_email
        self.session['auth_provider'] = session_user.auth_provider
        self.session['email'] = session_user.email
        self.session['profile_url'] = session_user.profile_url
        self.session['formatted_name'] = session_user.formatted_name
        self.session['first_name'] = session_user.first_name
        self.session['last_name'] = session_user.last_name
        self.session['middle_name'] = session_user.middle_name
        self.session['prefix'] = session_user.prefix
        self.session['suffix'] = session_user.suffix

        self.session['gender'] = session_user.gender
        self.session['phone_number'] = session_user.phone_number
        self.session['photo'] = session_user.photo

        self.session['birthdate'] = session_user.birthdate
        self.session['birthdate_day'] = session_user.birthdate_day
        self.session['birthdate_month'] = session_user.birthdate_month
        self.session['birthdate_year'] = session_user.birthdate_year

        self.session['address_formatted'] = session_user.address_formatted
        self.session['address_state_province'] = session_user.address_state_province
        self.session['address_street_name'] = session_user.address_street_name
        self.session['address_locality'] = session_user.address_locality
        self.session['address_zip_code'] = session_user.address_zip_code
        self.session['address_country'] = session_user.address_country

        self.session['is_logged_in'] = True

    def log_out(self):
        self.session['is_logged_in'] = False

    def is_logged_in(self):
        return self.session['is_logged_in']

    def is_user_authorized(self):
        retval = models.AUTH_LEVEL_NEW_USER
        session_user = self.get_session_user()
        if session_user:
            auth_user = models.User.get_user_from_identifier(session_user.identifier)
            logging.info('[session_user profile] ' + str(auth_user))
            if auth_user:
                retval = models.AUTH_LEVEL_REGISTERED_USER
                if auth_user.is_active and not auth_user.is_deleted:
                    retval = models.AUTH_LEVEL_ACTIVATED_USER
        return retval

class AuthorizedRequestHandler(SessionRequestHandler):
    pass

def render_template(template_name, **context):
	template = jinja_env.get_template(template_name)
	new_context = {}
	new_context.update(config.TEMPLATE_BUILTINS)
	new_context.update(context)
	return template.render(new_context)

from datetime import datetime

def get_iso_datetime_string(date_object):
  return date_object.strftime('%Y-%m-%dT%H:%M:%S')

def get_gravatar_url(email_address):
    import urllib, hashlib
    size = 40
    gravatar_url = "http://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({
        'gravatar_id': hashlib.md5(email_address).hexdigest(),
        'size': str(size)
        })
    return gravatar_url

def split_emails(email_string, pattern=r'[,;\s]'):
    pattern = re.compile(pattern)
    return [i for i in re.split(pattern, email_string) if i]

