#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
from datetime import datetime, timedelta
from google.appengine.api import memcache
from google.appengine.ext import db
try:
    import json
except ImportError:
    from django.utils import simplejson as json
import calendar as cal
from data import countries, calendar
import properties
from counter import Counter
from decimal import Decimal

FETCH_ALL_VALUES = 1000
DEFAULT_CACHE_TIMEOUT = 30   # 30 seconds.

# cache time out values in seconds.
FIVE_SECONDS = 5
TEN_SECONDS = 10
THIRTY_SECONDS = 30
ONE_MINUTE = 60
TWO_MINUTES = 120
FIVE_MINUTES = 300
TEN_MINUTES = FIVE_MINUTES * 2
TWENTY_MINUTES = FIVE_MINUTES * 4
THIRTY_MINUTES = FIVE_MINUTES * 6
HALF_HOUR = THIRTY_MINUTES
ONE_HOUR = HALF_HOUR * 2
TWELVE_HOURS = ONE_HOUR * 12
TWENTY_FOUR_HOURS = TWELVE_HOURS * 2
ONE_DAY = TWENTY_FOUR_HOURS
TWO_DAYS = ONE_DAY * 2
HALF_DAY = TWELVE_HOURS

HINT_QUESTIONS = {
    'mothers_maiden_name': "What is your mother's maiden name?",
    'name_of_pet': "What is the name of your pet?",
    'first_school_teacher': "Who was your first school teacher?",
    'first_phone_number': "What was your first phone number?",
    'favorite_passtime': "What is your favorite passtime?",
}
HINT_QUESTIONS_TUPLE_MAP = [(v,k) for k, v in HINT_QUESTIONS.iteritems()]
HINT_QUESTIONS_TUPLE_MAP.sort()
HINT_QUESTIONS_CHOICES = [k for k, v in HINT_QUESTIONS.iteritems()]
COUNTRIES_LIST = countries.COUNTRIES_SELECTION_LIST
MONTH_LIST = calendar.MONTH_NAMES

current_year = datetime.utcnow().year

BLOG_START_YEAR = 2009
BLOG_YEAR_LIST = range(BLOG_START_YEAR, current_year + 1)
YEAR_LIST = range(1900, current_year)
MILS_YEAR_LIST = range(1948, current_year + 1)[::-1]
MINIMUM_AGE_LIMIT = 18
BIRTH_YEAR_LIST = YEAR_LIST[:-(MINIMUM_AGE_LIMIT - 1)][::-1]
DEFAULT_BIRTHDATE = (BIRTH_YEAR_LIST[0], 1, 1)
DEFAULT_BIRTHDATE_STRING = '%d-%d-%d' % DEFAULT_BIRTHDATE

GENDER_CHOICES = (
    'male',
    'female',
)

BLOG_CONTENT_TYPES = (
    'markdown',
    'textile',
)

T_SHIRT_SIZES = {
    'small': 'Small',
    'medium': 'Medium',
    'large': 'Large',
    'extra_large': 'Extra Large',
}
T_SHIRT_TYPES_TUPLE_MAP = [(k, v) for k, v in T_SHIRT_SIZES.iteritems()]
T_SHIRT_TYPES = [k for k, v in T_SHIRT_SIZES.iteritems()]
T_SHIRT_TYPES.sort()

RAILWAY_LINES = {
    'western': 'Western',
    'central': 'Central',
    'harbor': 'Harbor',
    'other': 'Out of Mumbai',
}
RAILWAY_LINE_TYPES = [k for k, v in RAILWAY_LINES.iteritems()]
RAILWAY_LINE_TYPES.sort()
RAILWAY_LINES_TUPLE_MAP = [(k, v) for k, v in RAILWAY_LINES.iteritems()]

ADDRESS_TYPES = (
    'home',
    'residence',
    'work',
    'correspondence',
    'permanent',
    'temporary',
    'other',
)

PHONE_TYPES = (
    'mobile',
    'home',
    'work',
    'fax',
    'pager',
    'other',
)

PAYMENT_MODES = (
    'electronic',
    'cheque',
    'cash',
)

AUTH_LEVEL_NEW_USER = 0
AUTH_LEVEL_REGISTERED_USER = 1
AUTH_LEVEL_ACTIVATED_USER = 2

MAIL_TEMPLATE_CHOICES = [
    'jinja2',
]

ARTICLE_SECTION_TYPE_ALUMNI = 'alumni'
ARTICLE_SECTION_TYPE_STUDENT = 'student'
ARTICLE_SECTION_TYPES = [ARTICLE_SECTION_TYPE_ALUMNI, ARTICLE_SECTION_TYPE_STUDENT]


def clear_datastore(including_articles=False):
    db.delete(User.all())
    db.delete(Person.all())
    db.delete(PersonAddress.all())
    db.delete(PersonPhone.all())
    db.delete(OpenID.all())
    db.delete(Book.all())
    db.delete(UserBookOrder.all())
    if including_articles:
        db.delete(Article.all())
        db.delete(ArticleComment.all())

class RegularModel(db.Expando):
    is_deleted = db.BooleanProperty(default=False)
    is_starred = db.BooleanProperty(default=False)
    is_active = db.BooleanProperty(default=False)
    when_created = db.DateTimeProperty(auto_now_add=True)
    when_modified = db.DateTimeProperty(auto_now=True)
    #who_modified = db.StringProperty()

    def to_json_dict(self, *props):
        properties = self.properties()
        if props:
            serializable_properties = props
        else:
            serializable_properties = getattr(self, '__serialize__', [])
            if not serializable_properties:
                serializable_properties = properties.keys()
            else:
                serializable_properties.extend([
                    'is_deleted',
                    'is_starred',
                    'is_active',
                    'when_created',
                    'when_modified',
                    ])
        output = {}
        output['key'] = str(self.key())
        for prop in set(serializable_properties):
            v = properties[prop]
            if isinstance(v, db.DateTimeProperty) or isinstance(v, db.DateProperty):
                convert_function = (lambda d: d.strftime('%Y-%m-%dT%H:%M:%S'))
                output[prop] = convert_function(getattr(self, prop))
            elif isinstance(v, db.ReferenceProperty):
                str_key = str(getattr(self, prop).key())
                output[prop] = str_key
                #output[prop + '_key'] = str_key
            else:
                output[prop] = getattr(self, prop)
        return output

    def to_json(self, *props):
        json_dict = self.to_json_dict(*props)
        return json.dumps(json_dict)

class Api(RegularModel):
    name = db.StringProperty()
    api_key = db.StringProperty()
    mode = db.StringProperty(choices=[config.MODE_PRODUCTION, config.MODE_DEVELOPMENT])
    
    @classmethod
    def get_api_key(cls, name, mode=config.DEPLOYMENT_MODE):
        cache_key = 'Api.api_key.' + name + '.' + mode
        api_key = memcache.get(cache_key)
        if not api_key:
            api = db.Query(Api).filter('name =', name).filter('mode =', mode).get()
            api_key = api.api_key
            memcache.set(cache_key, api_key, 7200)
        return api_key
        
    @classmethod
    def set_api_key(cls, name, api_key, mode=config.DEPLOYMENT_MODE):
        api = db.Query(Api).filter('name =', name).filter('mode =', mode).get()
        api.api_key = api_key
        cache_key = 'Api.api_key.' + name + '.' + mode
        memcache.set(cache_key, api_key)

class FirstAlumniMeetRegistrant(RegularModel):
    email = db.EmailProperty(required=True)
    company = db.StringProperty()
    enrollment_fee = db.StringProperty()
    designation = db.StringProperty()
    first_name = db.StringProperty()
    graduation_year = db.IntegerProperty()
    last_name = db.StringProperty()
    nearest_railway_line = db.StringProperty(choices=RAILWAY_LINE_TYPES)
    payment_mode = db.StringProperty()
    phone_number = db.StringProperty()
    t_shirt_size = db.StringProperty(choices=T_SHIRT_TYPES)

    @classmethod
    def get_person_from_email(cls, email):
        cache_key = 'FirstAlumniMeetRegistrant.email=' + email
        person = memcache.get(cache_key)
        if not person:
            person = db.Query(FirstAlumniMeetRegistrant).filter('email =', email).get()
            memcache.set(cache_key, person, 400)
        return person

class Mail(RegularModel):
    
    subject = db.StringProperty()
    body = db.TextProperty()
    to_users = db.StringProperty()
    to_emails = db.StringListProperty()
    when_sent = db.DateTimeProperty()

    @classmethod
    def get_all(cls):
        cache_key = 'Mail.get_all'
        mails = memcache.get(cache_key)
        if not mails:
            mails = db.Query(Mail).order('-when_sent').order('-when_modified').order('-when_created').fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, mails, 15)
        return mails

class MailReceiver(RegularModel):
    email = db.EmailProperty()
    mail = db.ReferenceProperty(collection_name='receivers')

"""
class MailerTemplate(RegularModel):
    name = db.StringProperty()
    content = db.TextProperty()
    content_type = db.StringProperty(choices=MAIL_TEMPLATE_CHOICES)

class MailerList(RegularModel):
    name = db.StringProperty()

class MailerEmailAddress(RegularModel):
    email = db.EmailProperty()
    name = db.StringProperty()
    mailer_list = db.ReferenceProperty(MailerList, 'email_addresses')
"""

class User(RegularModel):
    username = db.StringProperty(required=True)
    signin_email = db.EmailProperty()
    email = db.EmailProperty(required=True)
    corporate_email = db.EmailProperty()
    nickname = db.StringProperty()
    identifier = db.StringProperty(required=True)
    photo = db.URLProperty()
    auth_provider = db.StringProperty()

    # Preferences
    enable_notifications = db.BooleanProperty(default=True)
    enable_administrator_contact = db.BooleanProperty(default=True)
    enable_public_profile = db.BooleanProperty(default=True)

    # Flags
    wants_activation = db.BooleanProperty(default=False)
    has_updated_profile = db.BooleanProperty(default=False)
    #has_received_email_thank_you_for_registering = db.BooleanProperty(default=False)
    #is_premium_user = db.BooleanProperty(default=False)
    is_premium = db.BooleanProperty(default=False)
    #is_rejected = db.BooleanProperty(default=False)

    def __str__(self):
        return 'username: %s, nickname: %s, email: %s, identifier: %s, auth_provider: %s' % (self.username, self.nickname, self.email, self.identifier, self.auth_provider)

    @classmethod
    def get_user_count(cls):
        return Counter('User.user_count').count

    @classmethod
    def set_user_count(cls, count):
        Counter('User.user_count').count = count
    #user_count = property(get_user_count, set_user_count)

    @classmethod
    def increment_user_count(cls, incr=1):
        Counter('User.user_count').increment(incr=incr)

    @classmethod
    def decrement_user_count(cls):
        user_count = Counter('User.user_count')
        if user_count.count > 0:
            user_count.increment(incr=-1)

    # Approved participants count
    @classmethod
    def get_approved_user_count(cls):
        return Counter('User.approved_user_count').count

    @classmethod
    def set_approved_user_count(cls, count):
        Counter('User.approved_user_count').count = count

    @classmethod
    def increment_approved_user_count(cls, incr=1):
        Counter('User.approved_user_count').increment(incr=incr)

    @classmethod
    def decrement_approved_user_count(cls):
        user_count = Counter('User.approved_user_count')
        if user_count.count > 0:
            user_count.increment(incr=-1)


    # deleted participants count
    @classmethod
    def get_deleted_user_count(cls):
        return Counter('User.deleted_user_count').count

    @classmethod
    def set_deleted_user_count(cls, count):
        Counter('User.deleted_user_count').count = count

    @classmethod
    def increment_deleted_user_count(cls, incr=1):
        Counter('User.deleted_user_count').increment(incr=incr)

    @classmethod
    def decrement_deleted_user_count(cls):
        user_count = Counter('User.deleted_user_count')
        if user_count.count > 0:
            user_count.increment(incr=-1)


    @classmethod
    def purge_deleted(cls):
        db.delete(db.Query(User).filter('is_deleted', True))

    @classmethod
    def get_all_by_filter(cls, filter_name):
        cache_key = 'User.get_all_by_filter.' + filter_name
        users = memcache.get(cache_key)
        if not users:
            #condition = filters.get(filter_name, None)
            if filter_name == 'approved':
                users = db.Query(User).filter('is_active =', True).filter('is_deleted =', False)
            elif filter_name == 'registered':
                users = db.Query(User).filter('is_active =', False).filter('is_deleted =', False)
            elif filter_name == 'deleted':
                users = db.Query(User).filter('is_deleted =', True)
            elif filter_name == 'none':
                users = []
            else:
                users = db.Query(User)
            if users:
                users = users.fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, users)
        return users

    @classmethod
    def get_all(cls):
        cache_key = 'User.get_all'
        users = memcache.get(cache_key)
        if not users:
            users = db.Query(User).order('-when_created').order('nickname').fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, users, 15)
        return users

    @classmethod
    def get_user_from_identifier(cls, identifier):
        cache_key = ''.join(['User.get_user_from_identifier(', identifier, ')'])
        cached_user = memcache.get(cache_key)
        if cached_user is not None:
            return cached_user
        else:
            user = db.Query(User).filter('identifier', identifier).get()
            memcache.set(cache_key, user, ONE_MINUTE)
            return user

    @classmethod
    def get_user_from_email_and_identifier(cls, email, identifier):
        cache_key = ''.join(['User.get_user_from_email_and_identifier(', email, ' ,', identifier, ')'])
        cached_user = memcache.get(cache_key)
        if cached_user is not None:
            return cached_user
        else:
            user = db.Query(User).filter('email', email).filter('identifier', identifier).get()
            memcache.set(cache_key, user, ONE_MINUTE)
            return user

class UserHostInformation(RegularModel):
    ip_address = db.StringProperty()
    http_user_agent = db.StringProperty()
    http_accept_language = db.StringProperty()
    http_accept_charset = db.StringProperty()
    http_accept_encoding = db.StringProperty()
    http_accept = db.StringProperty()
    http_referer = db.StringProperty()

    user = db.ReferenceProperty(User, 'host_information_set')

class OpenID(RegularModel):
    username = db.StringProperty()
    nickname = db.StringProperty()
    email = db.EmailProperty()
    auth_provider = db.StringProperty()
    identifier = db.StringProperty()
    profile_url = db.StringProperty()
    photo = db.URLProperty()

    is_primary_id = db.BooleanProperty(default=False)

    user = db.ReferenceProperty(User, collection_name='openids')

class Person(RegularModel):
    first_name = db.StringProperty()
    #middle_name = db.StringProperty()
    last_name = db.StringProperty()
    birthdate = db.DateProperty()
    designation = db.StringProperty()
    company = db.StringProperty()
    t_shirt_size = db.StringProperty(choices=T_SHIRT_TYPES)
    gender = db.StringProperty(choices=GENDER_CHOICES)
    graduation_year = db.IntegerProperty()
    is_student = db.BooleanProperty(default=False)

    user = db.ReferenceProperty(User, collection_name='people_singleton')

    def __str__(self):
        return ' '.join([self.first_name, self.last_name])

class MailingAddress(RegularModel):
    address_type = db.StringProperty(choices=ADDRESS_TYPES)
    address_line = db.PostalAddressProperty()
    apartment = db.StringProperty()
    state_province = db.StringProperty()
    city = db.StringProperty()
    zip_code = db.StringProperty()
    street_name = db.StringProperty()
    country = db.StringProperty(choices=countries.ISO_ALPHA_3_CODES)
    landmark = db.StringProperty()
    nearest_railway_line = db.StringProperty(choices=RAILWAY_LINE_TYPES)

class PersonAddress(MailingAddress):
    person = db.ReferenceProperty(Person, collection_name='addresses')

class Phone(RegularModel):
    phone_type = db.StringProperty(choices=PHONE_TYPES)
    number = db.StringProperty()

    def __str__(self):
        return ' '.join([self.number, '(', self.phone_type, ')'])

class PersonPhone(Phone):
    person = db.ReferenceProperty(Person, collection_name='phones')

class Sponsor(RegularModel):
    title = db.StringProperty()
    description = db.StringProperty()
    website_url = db.URLProperty()
    
    @classmethod
    def get_all(cls):
        cache_key = 'Sponsor.get_all'
        sponsors = memcache.get(cache_key)
        if not sponsors:
            sponsors = db.Query(Sponsor).fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, sponsors, 120)
        return sponsors

class SponsorImage(RegularModel):
    sponsor = db.ReferenceProperty(Sponsor, collection_name='images')
    image = db.BlobProperty()
    image_filename = db.StringProperty()
    image_extension = db.StringProperty()
    image_type = db.StringProperty()

# Blog
class Article(RegularModel):
    title = db.StringProperty()
    slug_title = db.StringProperty()
    subtitle = db.StringProperty()
    content = db.TextProperty()
    content_html = db.TextProperty()
    is_draft = db.BooleanProperty(default=True)
    tags = db.ListProperty(db.Category)
    when_published = db.DateTimeProperty(auto_now_add=True)
    section_type = db.StringProperty(choices=ARTICLE_SECTION_TYPES)
    author = db.UserProperty(auto_current_user=True)

    @classmethod
    def get_all(cls):
        cache_key = 'Article.get_all'
        articles = memcache.get(cache_key)
        if not articles:
            articles = db.Query(Article).order('title').fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, articles, 30)
        return articles

    @classmethod
    def get_article_for_day_with_slug(cls, year, month, day, slug_title):
        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = start_date + timedelta(1)
        cache_key = 'Article.get_article_for_day_with_slug' + str(year) + str(month) + str(day) + slug_title
        article = memcache.get(cache_key)
        if not article:
            article = db.Query(Article) \
                .filter('slug_title =', slug_title) \
                .filter('is_deleted =', False) \
                .filter('is_active =', True) \
                .filter('when_published >=', start_date) \
                .filter('when_published <', end_date) \
                .get()
            memcache.set(cache_key, article, ONE_MINUTE)
        return article

    @classmethod
    def get_all_published_for_month(cls, year, month):
        first_weekday, number_of_days = cal.monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, number_of_days, 23, 59, 59)
        cache_key = 'Article.get_all_published_for_month' + str(year) + str(month)
        articles = memcache.get(cache_key)
        if not articles:
            articles = db.Query(Article) \
                .order('-when_published') \
                .filter('is_deleted =', False) \
                .filter('is_active =', True) \
                .filter('section_type =', ARTICLE_SECTION_TYPE_ALUMNI) \
                .filter('when_published >=', start_date) \
                .filter('when_published <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, articles, ONE_MINUTE)
        return articles

    @classmethod
    def get_latest_published(cls, count=5):
        cache_key = 'Article.get_latest_published' + str(count)
        articles = memcache.get(cache_key)
        if not articles:
            articles = db.Query(Article) \
                .order('-when_published') \
                .filter('is_deleted =', False) \
                .filter('is_active =', True) \
                .filter('section_type =', ARTICLE_SECTION_TYPE_ALUMNI) \
                .fetch(count)
            memcache.set(cache_key, articles, ONE_MINUTE)
        return articles

    @classmethod
    def get_latest_published_student(cls, count=5):
        cache_key = 'Article.get_latest_published_student' + str(count)
        articles = memcache.get(cache_key)
        if not articles:
            articles = db.Query(Article) \
                .order('-when_published') \
                .filter('is_deleted =', False) \
                .filter('is_active =', True) \
                .filter('section_type =', ARTICLE_SECTION_TYPE_STUDENT) \
                .fetch(count)
            memcache.set(cache_key, articles, ONE_MINUTE)
        return articles

    @classmethod
    def get_all_published_student_articles_for_month(cls, year, month):
        first_weekday, number_of_days = cal.monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, number_of_days, 23, 59, 59)
        cache_key = 'Article.get_all_published_student_articles_for_month' + str(year) + str(month)
        articles = memcache.get(cache_key)
        if not articles:
            articles = db.Query(Article) \
                .order('-when_published') \
                .filter('is_deleted =', False) \
                .filter('is_active =', True) \
                .filter('section_type =', ARTICLE_SECTION_TYPE_STUDENT) \
                .filter('when_published >=', start_date) \
                .filter('when_published <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, articles, ONE_MINUTE)
        return articles

class ArticleComment(RegularModel):
    title = db.StringProperty()
    content = db.StringProperty()
    author = db.ReferenceProperty(User, collection_name='comments')
    article = db.ReferenceProperty(Article, collection_name='comments')

class Book(RegularModel):
    title = db.StringProperty()
    authors = db.StringProperty()
    isbn_10 = db.StringProperty()
    isbn_13 = db.StringProperty()
    is_cover_available = db.BooleanProperty(default=False)
    info_url = db.URLProperty()

    def __str__(self):
        return ', '.join(['Title: ' + self.title,
            'ISBN 10: ' + self.isbn_10,
            'ISBN 13: ' + self.isbn_13])

    @classmethod
    def get_latest(cls, count=10):
        cache_key = 'Book.get_latest(count=' + str(count) + ')'
        books = memcache.get(cache_key)
        if not books:
            books = db.Query(Book).order('when_modified').order('title').fetch(count)
            memcache.set(cache_key, books, 120)
        return books

    @classmethod
    def get_all(cls):
        cache_key = 'Book.get_all'
        books = memcache.get(cache_key)
        if not books:
            books = db.Query(Book).order('title').fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, books, 120)
        return books

    @classmethod
    def get_all_books(cls):
        cache_key = 'Book.get_all_books'
        cached_value = memcache.get(cache_key)
        if cached_value:
            return cached_value
        else:
            books = db.Query(Book).order('title').filter('is_deleted', False).fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, books, TEN_SECONDS)
            return books

class UserBookOrder(RegularModel):
    user = db.ReferenceProperty(User, collection_name='users')
    book = db.ReferenceProperty(Book, collection_name='books')

class AboutUs(RegularModel):
    content = db.TextProperty()

class TrainingProgram(RegularModel):
    title = db.StringProperty()
    venue = db.StringProperty()
    when_from = db.DateTimeProperty()
    when_to = db.DateTimeProperty()
    faculties = db.StringListProperty()
    faculty = db.StringProperty()
    when_registration_ends = db.DateTimeProperty()
    when_payment_is_calculated = db.DateTimeProperty()
    is_registration_closed = db.BooleanProperty(default=False)
    is_canceled = db.BooleanProperty(default=False)
    final_price = properties.DecimalProperty(default=Decimal('0.00'))
    max_participants = db.IntegerProperty()
    participants = db.ReferenceProperty(User, 'training_programs')
    brochure_url = db.URLProperty()
    is_payment_mail_queued = db.BooleanProperty(default=False)
    description = db.TextProperty()

    # Active participants count
    def get_participant_count(self):
        participant_count = Counter('TrainingProgram.participant_count' + str(self.key()))
        return participant_count.count

    def set_participant_count(self, count):
        participant_count = Counter('TrainingProgram.participant_count' + str(self.key()))
        participant_count.count = count
    participant_count = property(get_participant_count, set_participant_count)

    def increment_participant_count(self, incr=1):
        participant_count = Counter('TrainingProgram.participant_count' + str(self.key()))
        participant_count.increment(incr=incr)

    def decrement_participant_count(self):
        participant_count = Counter('TrainingProgram.participant_count' + str(self.key()))
        if participant_count.count > 0:
            participant_count.increment(incr=-1)

    # Total participants count
    def get_total_participant_count(self):
        total_participant_count = Counter('TrainingProgram.total_participant_count' + str(self.key()))
        return total_participant_count.count

    def set_total_participant_count(self, count):
        total_participant_count = Counter('TrainingProgram.total_participant_count' + str(self.key()))
        total_participant_count.count = count
    total_participant_count = property(get_total_participant_count, set_total_participant_count)

    def increment_total_participant_count(self, incr=1):
        total_participant_count = Counter('TrainingProgram.total_participant_count' + str(self.key()))
        total_participant_count.increment(incr=incr)

    def decrement_total_participant_count(self):
        total_participant_count = Counter('TrainingProgram.total_participant_count' + str(self.key()))
        if total_participant_count.count > 0:
            total_participant_count.increment(incr=-1)

    def get_fees_sorted_by_count(self):
        key = str(self.key())
        cache_key = 'TrainingProgram.' + key + 'fees.sorted'
        fees = memcache.get(cache_key)
        if not fees:
            fees = db.Query(TrainingProgramFee) \
                .filter('training_program =', self) \
                .filter('is_deleted =', False) \
                .order('for_participant_count') \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, fees, 120)
        return fees
 
    @property
    def registrants_in_chronological_order(self):
        key = str(self.key())
        cache_key = "TrainingProgramRegistrants_for" + key + "chronologically.sorted"
        registrants = memcache.get(cache_key)
        if not registrants:
            registrants = db.Query(TrainingProgramRegistrant) \
                .filter("training_program =", self) \
                .filter("is_deleted =", False) \
                .order("when_created") \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, registrants)
        return registrants
 
    @classmethod
    def get_all_closable_for_date(cls, year, month, day):
        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = datetime(year, month, day, 23, 59, 59)

        cache_key = 'TrainingPrograms.approved.all_closable_for_date' + str(year) + str(month) + str(day)
        training_programs = memcache.get(cache_key)
        if not training_programs:
            training_programs = db.Query(TrainingProgram) \
                .order('when_registration_ends') \
                .order('title') \
                .filter('is_deleted = ', False) \
                .filter('is_active = ', True) \
                .filter('when_registration_ends >=', start_date) \
                .filter('when_registration_ends <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, training_programs, 15)
        return training_programs

    @classmethod
    def get_all_payable_for_date(cls, year, month, day):
        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = datetime(year, month, day, 23, 59, 59)

        cache_key = 'TrainingPrograms.approved.all_payable_for_date' + str(year) + str(month) + str(day)
        training_programs = memcache.get(cache_key)
        if not training_programs:
            training_programs = db.Query(TrainingProgram) \
                .order('when_payment_is_calculated') \
                .order('title') \
                .filter('is_deleted = ', False) \
                .filter('is_active = ', True) \
                .filter('is_payment_mail_queued = ', False) \
                .filter('when_payment_is_calculated >=', start_date) \
                .filter('when_payment_is_calculated <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, training_programs, 15)
        return training_programs

    @classmethod
    def get_all_approved_for_month(cls, year, month):
        first_weekday, number_of_days = cal.monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, number_of_days, 23, 59, 59)

        #t = datetime.utcnow()
        #today = datetime(t.year, t.month, t.day, 0, 0, 0)
        #if today < end_date:
        #    end_date = today

        cache_key = 'TrainingPrograms.approved' + str(year) + str(month)
        training_programs = memcache.get(cache_key)
        if not training_programs:
            training_programs = db.Query(TrainingProgram) \
                .order('when_registration_ends') \
                .order('title') \
                .filter('is_deleted = ', False) \
                .filter('is_active = ', True) \
                .filter('when_registration_ends >=', start_date) \
                .filter('when_registration_ends <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, training_programs, 10)
        return training_programs

    @classmethod
    def populate_datastore(cls):
        from datetime import datetime
        data = [
            dict(title='Program1',
                venue='Venue1',
                when_from=datetime(2009, 10, 20),
                when_to=datetime(2009, 10, 21),
                faculties=['Hmm', 'Foo', 'Bar'],
                faculty='Dr. Hmmm Pmmm.',
                when_registration_ends=datetime(2009, 9, 10),
                max_participants=20),
            dict(title='Program2',
                venue='Venue2',
                when_from=datetime(2009, 10, 20),
                when_to=datetime(2009, 10, 21),
                faculties=['Hamm', 'Faoo', 'Baar'],
                faculty='Dr. Hamm Fammm',
                when_registration_ends=datetime(2009, 9, 10),
                max_participants=21),
            dict(title='Program2',
                venue='Venue2',
                when_from=datetime(2009, 9, 20),
                when_to=datetime(2009, 9, 21),
                faculties=['Hemm', 'Feoo', 'Bear'],
                faculty='Dr. Hemm Femm',
                when_registration_ends=datetime(2009, 8, 10),
                max_participants=22),
        ]
        import random
        #ps = []
        fees = []
        for d in data:
            p = TrainingProgram(**d)
            p.put()
            for i in range(0, 2):
                f = TrainingProgramFee(fee_integer=random.choice([1000, 400, 600]),
                    for_participants_count=random.choice([20, 30, 25]))
                f.training_program = p
                fees.append(f)
        db.put(fees)

    @classmethod
    def clear_datastore(cls):
        db.delete(TrainingProgram.all())
        db.delete(TrainingProgramFee.all())

    @classmethod
    def get_all(cls):
        cache_key = 'TrainingPrograms.all_'
        training_programs = memcache.get(cache_key)
        if not training_programs:
            training_programs = db.Query(TrainingProgram) \
                .order('title') \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, training_programs, ONE_MINUTE)
        return training_programs

    @classmethod
    def get_all_published_for_month(cls, year, month):
        first_weekday, number_of_days = cal.monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, number_of_days, 23, 59, 59)
        cache_key = 'TrainingPrograms.published'
        training_programs = memcache.get(cache_key)
        if not training_programs:
            training_programs = db.Query(TrainingProgram) \
                .order('-when_published') \
                .order('title') \
                .filter('is_deleted', False) \
                .filter('is_active', True) \
                .filter('when_published >=', start_date) \
                .filter('when_published <=', end_date) \
                .fetch(FETCH_ALL_VALUES)
            memcache.set(cache_key, training_programs, ONE_MINUTE)
        return training_programs

class TrainingProgramRegistrant(RegularModel):
    full_name = db.StringProperty()
    email = db.EmailProperty()
    phone_number = db.StringProperty()
    company = db.StringProperty()
    designation = db.StringProperty()
    why_unregister = db.TextProperty()
    is_payment_received = db.BooleanProperty(default=False)
    training_program = db.ReferenceProperty(TrainingProgram, collection_name='registrants')

class TrainingProgramFee(RegularModel):
    for_participant_count = db.IntegerProperty(required=True)
    fee = properties.DecimalProperty(required=True)
    training_program = db.ReferenceProperty(TrainingProgram, collection_name='fees')

class TrainingProgramBrochure(RegularModel):
    brochure_content = db.BlobProperty()
    brochure_file_name = db.StringProperty()
    brochure_mime_type = db.StringProperty()
    training_program = db.ReferenceProperty(TrainingProgram, collection_name='brochures')

