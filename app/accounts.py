#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
import hashlib
import urllib
import logging
from datetime import datetime

from google.appengine.api import urlfetch, mail, memcache
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import apiproxy_errors
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from jinja2 import Environment, FileSystemLoader
#from recaptcha.client import captcha
from appengine_utilities.sessions import Session
from data.countries import COUNTRY_NAME_ISO_ALPHA_3_TABLE
from data.existing_users import USERS

from utils import get_gravatar_url, birthdate_to_string, birthdate_to_tuple, queue_mail_task, queue_task, dec, render_template, SessionUser, SessionRequestHandler, AuthorizedRequestHandler
import utils
from data import countries, calendar
import models

logging.basicConfig(level=logging.DEBUG)

class RPXTokenHandler(SessionRequestHandler):
    def get(self):
        token = self.request.get('token')
        url = config.RPX_NOW_API_AUTH_URL
        args = {
            'format': 'json',
            'apiKey': config.RPX_NOW_API_AUTH_KEY,
            'token': token,
        }
        api_response = urlfetch.fetch(url=url,
            payload=urllib.urlencode(args),
            method=urlfetch.POST,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            })
        json_dict = json.loads(api_response.content)
        logging.info('>>>>>>>>>>> rpx_handler: ' + api_response.content)

        if json_dict['stat'] == 'ok':
            profile = json_dict['profile']
            name = profile.get('name', {})
            address = profile.get('address', {})

            identifier = profile.get('identifier')
            cached_session_user = memcache.get('rpxnow_' + identifier)
            if cached_session_user:
                session_user = cached_session_user
            else:
                # Handle birthdate.
                birthdate = profile.get('birthday', models.DEFAULT_BIRTHDATE_STRING)
                birthdate_year, birthdate_month, birthdate_day = birthdate_to_tuple(birthdate)
                birthdate = birthdate_to_string(birthdate_year, birthdate_month, birthdate_day)
                email = profile.get('email', '')
                existing_user = USERS.get(email, {})

                session_user = SessionUser(
                    identifier = identifier,
                    username = profile.get('preferredUsername'),
                    nickname = profile.get('displayName', ''),
                    email = email,
                    verified_email = profile.get('verifiedEmail', ''),
                    auth_provider = profile.get('providerName', ''),
                    profile_url = profile.get('url', ''),
                    formatted_name = name.get('formatted', ''),
                    first_name = name.get('givenName', existing_user.get('first_name', '')),
                    last_name = name.get('familyName', existing_user.get('last_name', '')),
                    middle_name = name.get('middleName', ''),
                    prefix = name.get('honorificPrefix', ''),
                    suffix = name.get('honorificSuffix', ''),

                    gender = profile.get('gender', 'male'),
                    phone_number = profile.get('phoneNumber', existing_user.get('phone_number', '')),
                    photo = profile.get('photo', ''),
                    birthdate = birthdate,
                    birthdate_day = birthdate_day,
                    birthdate_month = birthdate_month,
                    birthdate_year = birthdate_year,

                    address_formatted = address.get('formatted', ''),
                    address_state_province = address.get('region', ''),
                    address_street_name = address.get('streetAddress', ''),
                    address_locality = address.get('locality', ''),
                    address_zip_code = address.get('postalCode', ''),
                    address_country = address.get('country', '')
                    )
                if session_user.nickname or session_user.formatted_name:
                    nickname = session_user.nickname if session_user.nickname else session_user.session_formatted_name
                    import re
                    nickname_split = re.compile('[ ._]').split(nickname)
                    if len(nickname_split) == 1:
                        if not session_user.first_name:
                            session_user.first_name = nickname
                    elif len(nickname_split) == 2:
                        if not session_user.first_name:
                            session_user.first_name = nickname_split[0]
                        if not session_user.last_name:
                            session_user.last_name = nickname_split[1]
                    elif len(nickname_split) >= 3:
                        if not session_user.first_name:
                            session_user.first_name = nickname_split[0]
                        if not session_user.middle_name:
                            session_user.middle_name = nickname_split[1]
                        if not session_user.last_name:
                            session_user.last_name = nickname_split[2]
                memcache.set(identifier, session_user, 1800)
            self.log_in(session_user)
            self.redirect('/account')
        else:
            self.redirect('/')

"""
class AccountLoginPage(SessionRequestHandler):
    def get(self):
        if self.get_session_user():
            self.redirect('/')
        else:
            rendered_response = render_template('login.html')
            self.response.out.write(rendered_response)
"""

class AccountPage(AuthorizedRequestHandler):
    def get(self):
        session_user = self.get_session_user()
        if session_user:
            auth_level = self.is_user_authorized()
            if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
                self.redirect('/account/activate/reminder/')
            elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
                self.redirect('/blog')
            values = dict(
                countries=models.COUNTRIES_LIST,
                month_list=models.MONTH_LIST,
                year_list=models.BIRTH_YEAR_LIST,
                phone_types=models.PHONE_TYPES,
                hint_questions=models.HINT_QUESTIONS_TUPLE_MAP,
                t_shirt_sizes=models.T_SHIRT_TYPES_TUPLE_MAP,
                gender_choices=models.GENDER_CHOICES,
                railway_lines=models.RAILWAY_LINES_TUPLE_MAP,
                mils_year_list=models.MILS_YEAR_LIST
            )
            email = session_user.email
            if email:
                existing_user = USERS.get(email, {})
                graduation_year = existing_user.get('graduation_year', models.MILS_YEAR_LIST[0])
                designation = existing_user.get('designation', '')
                company = existing_user.get('company', '')
                t_shirt_size = existing_user.get('t_shirt_size', 'small')
                nearest_railway_line = existing_user.get('nearest_railway_line', 'western')
                values.update({
                    'graduation_year': graduation_year,
                    'company': company,
                    'designation': designation,
                    't_shirt_size': t_shirt_size,
                    'nearest_railway_line': nearest_railway_line,
                    'phone_type': 'mobile',
                })
            values.update(session_user.to_dict())
            response = render_template('signup.html', **values)
            self.response.out.write(response)
        else:
            self.redirect('/')

    def post(self):
        session_user = self.get_session_user()

        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        birthdate_day = dec(self.request.get('birthdate_day'))
        birthdate_month = dec(self.request.get('birthdate_month'))
        birthdate_year = dec(self.request.get('birthdate_year'))
        company = self.request.get('company')
        designation = self.request.get('designation')
        gender = self.request.get('gender')
        t_shirt_size = self.request.get('t_shirt_size')
        email_address = self.request.get('email_address')
        corporate_email_address = self.request.get('corporate_email_address')
        railway_line = self.request.get('railway_line')
        graduation_year = dec(self.request.get('graduation_year'))

        if not session_user.email:
            session_user.email = email_address

        apartment = self.request.get('apartment')
        street_name = self.request.get('street_name')
        landmark = self.request.get('landmark')
        city = self.request.get('city')
        state_province = self.request.get('state_province')
        zip_code = self.request.get('zip_code')
        country = self.request.get('country')

        phone_number_count = int(self.request.get('phone_number_count'), 10)
        phone_numbers = []
        for i in range(1, phone_number_count+1):
            phone_number = self.request.get('phone_number_' + str(i))
            phone_type = self.request.get('phone_type_' + str(i))
            phone_numbers.append((phone_number, phone_type))

        #enable_notifications = True if self.request.get('enable_notifications') else False
        #enable_public_profile = True if self.request.get('enable_public_profile') else False
        #enable_administrator_contact = True if self.request.get('enable_administrator_contact') else False
        enable_notifications = True
        enable_public_profile = True
        enable_administrator_contact = True

        # Create database entries.
        to_store = []
        user = models.User(username=session_user.username,
            email=email_address,
            signin_email=session_user.email,
            identifier=session_user.identifier)
        if corporate_email_address:
            user.corporate_email = corporate_email_address
        user.nickname = first_name + ' ' + last_name
        user.enable_notifications = enable_notifications
        user.enable_public_profile = enable_public_profile
        user.enable_administrator_contact = enable_administrator_contact
        user.wants_activation = True
        user.has_updated_profile = True
        user.auth_provider = session_user.auth_provider
        user.is_active = False
        if session_user.photo:
            user.photo = session_user.photo
            user.gravatar = get_gravatar_url(email_address)
        user.put()

        person = models.Person()
        person.user = user
        person.first_name = first_name
        person.last_name = last_name
        person.company = company
        person.designation = designation
        person.birthdate = datetime(birthdate_year, birthdate_month, birthdate_day).date()
        person.gender = gender
        person.graduation_year = graduation_year
        person.t_shirt_size = t_shirt_size
        person.put()

        host_info = models.UserHostInformation()
        host_info.user = user
        host_info.ip_address = self.request.remote_addr
        host_info.http_user_agent = self.request.headers.get('User-Agent', '')
        host_info.http_accept_language = self.request.headers.get('Accept-Language', '')
        host_info.http_accept_encoding = self.request.headers.get('Accept-Encoding', '')
        host_info.http_accept_charset = self.request.headers.get('Accept-Charset', '')
        host_info.http_accept = self.request.headers.get('Accept', '')
        host_info.http_referer = self.request.headers.get('Referer', '')
        to_store.append(host_info)

        openid = models.OpenID(username=session_user.username)
        openid.nickname = session_user.nickname
        openid.email = session_user.email
        openid.auth_provider = session_user.auth_provider
        openid.identifier = session_user.identifier
        openid.profile_url = session_user.profile_url
        openid.user = user
        openid.is_primary_id = True
        to_store.append(openid)

        address_line = ', '.join([
            apartment,
            street_name,
            landmark,
            '' if railway_line == 'other' else models.RAILWAY_LINES.get(railway_line, '') + ' Railway Line',
            city,
            state_province + ' ' + zip_code,
            COUNTRY_NAME_ISO_ALPHA_3_TABLE.get(country, ''),
            ])
        address = models.PersonAddress(person=person,
            address_line=address_line,
            street_name=street_name,
            zip_code=zip_code,
            state_province=state_province,
            country=country,
            landmark=landmark,
            apartment=apartment,
            city=city,
            nearest_railway_line=railway_line,
            address_type='home')
        to_store.append(address)

        for (number, phone_type) in phone_numbers:
            if number.strip():
                phone = models.PersonPhone(person=person,
                    number=number,
                    phone_type=phone_type)
                to_store.append(phone)

        # Batch write all non-dependent entities.
        db.put(to_store)
        queue_mail_task(url='/worker/mail/signup_notification/' + str(user.key()), method='GET')
        rendered_template = render_template('activation_reminder.html')
        self.response.out.write(rendered_template)

class AccountActivateReminderPage(AuthorizedRequestHandler):
    def get(self):
        session_user = self.get_session_user()
        user = models.User.get_user_from_identifier(session_user.identifier)
        user.wants_activation = True
        user.put()

        cache_key = '/account/activate/reminder'
        cached_response = memcache.get(cache_key)
        if cached_response:
            self.response.out.write(cached_response)
        else:
            response = render_template('activation_reminder.html')
            memcache.set(cache_key, str(response), utils.STATIC_PAGE_CACHE_TIMEOUT)
            self.response.out.write(response)

class AccountLogoutPage(AuthorizedRequestHandler):
    def get(self):
        self.log_out()
        self.redirect('/')

urls = [
    ('/account/?', AccountPage),
    ('/account/rpx/?', RPXTokenHandler),
    ('/account/activate/reminder/?', AccountActivateReminderPage),
    ('/account/logout/?', AccountLogoutPage),
]
application = webapp.WSGIApplication(urls, debug=config.DEBUG)

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
	main()

