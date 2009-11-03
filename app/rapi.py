#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
import logging
from google.appengine.api import users, memcache
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from lovely.jsonrpc import wsgi
import models
from utils import dec, parse_iso_datetime_string, get_iso_datetime_string, queue_task, queue_mail_task
from data.countries import COUNTRY_NAME_ISO_ALPHA_3_TABLE
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

# Keep the timeout short because the admin expects the "freshest" data at "all" times.
DEFAULT_CACHE_TIMEOUT = 5 # seconds

def toggle_active(key):
    item = db.get(db.Key(key))
    item.is_active = not item.is_active
    item.put()
    return item.is_active

def toggle_starred(key):
    item = db.get(db.Key(key))
    item.is_starred = not item.is_starred
    item.put()
    return item.is_starred

def toggle_deleted(key):
    item = db.get(db.Key(key))
    item.is_deleted = not item.is_deleted
    item.put()
    return item.is_deleted

def toggle_premium(key):
    item = db.get(db.Key(key))
    item.is_premium = not item.is_premium
    item.put()
    return item.is_premium

def toggle_draft(key):
    item = db.get(db.Key(key))
    item.is_draft = not item.is_draft
    item.put()
    return item.is_draft

def toggle_keys_active(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_active = not item.is_active
        item_list.append(item)
    db.put(item_list)
    return keys

def toggle_keys_starred(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_starred = not item.is_starred
        item_list.append(item)
    db.put(item_list)
    return keys

def activate_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_active = True
        item_list.append(item)
    db.put(item_list)
    return keys

def activate_user_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_active = True
        item.wants_activation = False
        item_list.append(item)
        queue_mail_task(url='/worker/mail/account_activation_notification/' + key, method='GET')
    db.put(item_list)
    return keys

def deactivate_user_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_active = False
        item.wants_activation = False
        item_list.append(item)
    db.put(item_list)
    return keys
    
def deactivate_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_active = False
        item_list.append(item)
    db.put(item_list)
    return keys

def publish_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_draft = False
        item_list.append(item)
    db.put(item_list)
    return keys

def draft_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_draft = True
        item_list.append(item)
    db.put(item_list)
    return keys

def regularize_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_premium = False
        item_list.append(item)
    db.put(item_list)
    return keys

def premiumize_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_premium = True
        item_list.append(item)
    db.put(item_list)
    return keys

def star_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_starred = True
        item_list.append(item)
    db.put(item_list)
    return keys

def unstar_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_starred = False
        item_list.append(item)
    db.put(item_list)
    return keys

def delete_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_deleted = True
        item_list.append(item)
    db.put(item_list)
    return keys

def undelete_keys(keys):
    item_list = []
    for key in keys:
        item = db.get(db.Key(key))
        item.is_deleted = False
        item_list.append(item)
    db.put(item_list)
    return keys

delete_users = delete_keys
undelete_users = undelete_keys
star_users = star_keys
unstar_users = unstar_keys

def get_person_from_user(key):
    cache_key = 'json.get_person_from_user(' + key + ')'
    cached_result = memcache.get(cache_key)
    if cached_result:
        return cached_result
    else:
        user = db.get(db.Key(key))
        person = user.people_singleton[0]
        host_info =  db.Query(models.UserHostInformation).filter('user = ', user).get()  #user.host_information_set
        phones = []
        for phone in person.phones:
            phones.append(dict(
                key                = str(phone.key()),
                phone_number       = phone.number,
                phone_type         = phone.phone_type
            ))
        addresses = []
        for address in person.addresses:
            addresses.append(dict(
                key                  = str(address.key()),
                address_type         = address.address_type,
                #apartment            = address.apartment,
                #state_province       = address.state_province,
                #city                 = address.city,
                #zip_code             = address.zip_code,
                #street_name          = address.street_name,
                #country_code         = address.country,
                #country_name         = COUNTRY_NAME_ISO_ALPHA_3_TABLE.get(address.country, 'Unknown Country'),
                #landmark             = address.landmark,
                #nearest_railway_line = address.nearest_railway_line,
                address_line         = address.address_line
            ))
        corporate_email = user.corporate_email
        if not corporate_email:
            corporate_email = ''
        retval = dict(
                key           = str(person.key()),
                user_key      = str(person.user.key()),
                signin_email  = user.signin_email,
                corporate_email = corporate_email,
                first_name    = person.first_name, 
                last_name     = person.last_name,
                gender        = person.gender,
                company       = person.company,
                designation   = person.designation,
                graduation_year = person.graduation_year,
                t_shirt_size  = person.t_shirt_size,
                birthdate     = get_iso_datetime_string(person.birthdate),
                addresses     = addresses,
                phones        = phones,
                is_student    = person.is_student,
                when_created  = get_iso_datetime_string(user.when_created),
                http_user_agent = host_info.http_user_agent
            )
        memcache.set(cache_key, retval, DEFAULT_CACHE_TIMEOUT)
        return retval

def get_users():
    cache_key = 'api.get_users'
    cached_user_list = memcache.get(cache_key)
    if cached_user_list:
        return cached_user_list
    else:
        user_list = []
        users = models.User.all().order('nickname').fetch(models.FETCH_ALL_VALUES)
        for user in users:
            person = user.people_singleton[0]
            user_list.append(dict(username=user.username,
                email=user.email,
                signin_email=user.signin_email,
                corporate_email=user.corporate_email,
                nickname=user.nickname,
                key=str(user.key()),
                is_active=user.is_active,
                is_deleted=user.is_deleted,
                is_starred=user.is_starred,
                wants_activation=user.wants_activation,
                is_premium=user.is_premium,
                auth_provider=user.auth_provider,
                person_key=str(person.key()),
                graduation_year=person.graduation_year,
                when_created=get_iso_datetime_string(user.when_created)
            ))
        memcache.set(cache_key, user_list, DEFAULT_CACHE_TIMEOUT)
        return user_list

def get_books():
    book_list = []
    books = models.Book.all().order('title').fetch(models.FETCH_ALL_VALUES)
    for book in books:
        book_list.append(dict(title=book.title, 
            isbn_10=book.isbn_10, 
            isbn_13=book.isbn_13,
            author_name=book.author_name,
            key=str(book.key()),
            is_active=book.is_active,
            is_starred=book.is_starred,
            is_deleted=book.is_deleted,
            info_url=book.info_url
        ))
    return book_list

def get_book(key):
    book = db.get(db.Key(key))
    return dict(key=str(book.key()),
        title=book.title,
        author_name=book.author_name,
        isbn_10=book.isbn_10,
        isbn_13=book.isbn_13,
        is_active=book.is_active,
        is_starred=book.is_starred,
        is_deleted=book.is_deleted,
        info_url=book.info_url
    )

def is_openlibrary_cover_available(isbn):
    isbn = str(isbn)
    cache_key = 'cover_for_' + isbn
    cached_value = memcache.get(cache_key)
    if cached_value in (True, False):
        return cached_value
    else:
        from google.appengine.api import urlfetch
        cover_url = 'http://covers.openlibrary.org/b/isbn/' + isbn + '-S.jpg?default=false'
        result = urlfetch.fetch(cover_url)
        retval = False
        if result.status_code == 200:
            retval = True
        memcache.set(cache_key, retval, DEFAULT_CACHE_TIMEOUT)
        return retval

def save_book(key='', title='', author_name='', isbn_10='', isbn_13='', info_url=''):
    if key:
        book = db.get(db.Key(key))
    else:
        book = models.Book()
    book.title = title
    book.author_name = author_name
    book.isbn_10 = isbn_10
    book.isbn_13 = isbn_13
    if info_url:
        book.info_url = info_url
    book.put()
    return dict(key=str(book.key()),
        title=book.title,
        author_name=book.author_name,
        isbn_10=book.isbn_10,
        isbn_13=book.isbn_13,
        is_active=book.is_active,
        is_starred=book.is_starred,
        is_deleted=book.is_deleted,
        info_url=book.info_url
    )

def get_articles():
    cache_key = 'api.get_articles'
    cached_articles = memcache.get(cache_key)
    if cached_articles:
        return cached_articles
    else:        
        articles_list = []
        articles = models.Article.all().order('-when_published').fetch(models.FETCH_ALL_VALUES)
        for article in articles:
            articles_list.append(dict(title=article.title,
                is_draft=article.is_draft,
                when_published=get_iso_datetime_string(article.when_published),
                when_created=get_iso_datetime_string(article.when_created),
                key=str(article.key()),
                author_nickname=article.author.nickname(),
                author_email=article.author.email(),
                is_starred=article.is_starred,
                is_deleted=article.is_deleted
            ))
        memcache.set(cache_key, articles_list, DEFAULT_CACHE_TIMEOUT)
        return articles_list
        
def get_article(key):
    article = db.get(db.Key(key))
    return dict(title=article.title,
        is_draft=article.is_draft,
        key=str(article.key()),
        when_published=get_iso_datetime_string(article.when_published),
        when_created=get_iso_datetime_string(article.when_created),
        author_nickname=article.author.nickname(),
        author_email=article.author.email(),
        content=article.content,
        is_starred=article.is_starred,
        is_deleted=article.is_deleted
    )
    
def get_article_content(key):
    article = db.get(db.Key(key))
    return dict(key=key, 
        content=article.content
    )
    
def save_article(key='', title='', content='', is_draft=''):
    if key:
        article = db.get(db.Key(key))
    else:
        article = models.Article()
    article.title = title
    article.content = content
    article.is_draft = is_draft
    article.author = users.get_current_user()
    article.put()
    return dict(title=article.title,
        is_draft=article.is_draft,
        key=str(article.key()),
        when_published=get_iso_datetime_string(article.when_published),
        when_created=get_iso_datetime_string(article.when_created),
        author_nickname=article.author.nickname(),
        author_email=article.author.email(),
        #content=article.content,
        is_starred=article.is_starred,
        is_deleted=article.is_deleted
    )


def save_training_program(key='', title='', venue='', faculty='', 
        when_from='',
        when_to='',
        when_registration_ends='',
        participation_counts=[], 
        participation_fees=[]):
    if key:
        training_program = db.get(db.Key(key))
    else:
        training_program = models.TrainingProgram
    training_program.title = title
    training_program.venue = venue
    training_program.faculty = faculty
    training_program.when_from = parse_iso_datetime_string(when_from)
    training_program.when_to = parse_iso_datetime_string(when_to)
    training_program.when_registration_ends = parse_iso_datetime_string(when_registration_ends)
    training_program.put()
    
    fees = []
    for count, fee in izip(participation_counts, participation_fees):
        tpfee = models.TrainingProgramFee()
        tpfee.for_participation_count = count
        if '.' in fee:
            fee_integer, fee_fraction = fee.split('.')
        else:
            fee_integer, fee_fraction = fee, '0'
        tpfee.fee_integer = dec(fee_integer)
        tpfee.fee_fraction = dec(fee_fraction)
        tpfee.training_program = training_program
        fees.append(tpfee)
    db.put(fees)

def get_training_program(key):
    cache_key = 'api.get_training_program.json.' + key
    cached_value = memcache.get(cache_key)
    if cached_value:
        return cached_value
    else:
        training_program = db.get(db.Key(key))
        fees = [fee.to_json_dict('fee_integer', 'fee_fraction', 'for_participants_count') for fee in training_program.fees]
        training_program_json_dict = training_program.to_json_dict(
            'title',
            'venue',
            'when_from',
            'when_to',
            'when_registration_ends',
            'max_participants',
            'faculty',
            'is_starred',
            'is_deleted',
            'is_active'
        )
        training_program_json_dict['fees'] = fees
        memcache.set(cache_key, training_program_json_dict, DEFAULT_CACHE_TIMEOUT)
        return training_program_json_dict

def get_training_programs():
    cache_key = 'api.get_training_programs'
    cached_values = memcache.get(cache_key)
    if cached_values:
        return cached_values
    else:
        training_programs = models.TrainingProgram.get_all()   
        training_programs_list = []
        
        for training_program in training_programs:            
            fees = [fee.to_json_dict('fee_integer', 'fee_fraction', 'for_participants_count') for fee in training_program.fees]
            training_program_json_dict = training_program.to_json_dict(
                'title',
                'venue',
                'when_from',
                'when_to',
                'when_registration_ends',
                'max_participants',
                'faculty',
                'is_starred',
                'is_deleted',
                'is_active')
            training_program_json_dict['fees'] = fees
            training_programs_list.append(training_program_json_dict)
        memcache.set(cache_key, training_programs_list, DEFAULT_CACHE_TIMEOUT)
        return training_programs_list

def main():
    application = wsgi.WSGIJSONRPCApplication()
    
    application.register_method(activate_keys, 'activate_keys')
    application.register_method(deactivate_keys, 'deactivate_keys')
    application.register_method(star_keys, 'star_keys')
    application.register_method(unstar_keys, 'unstar_keys')
    application.register_method(delete_keys, 'delete_keys')
    application.register_method(undelete_keys, 'undelete_keys')
    application.register_method(toggle_starred, 'toggle_starred')
    application.register_method(toggle_active, 'toggle_active')
    application.register_method(toggle_deleted, 'toggle_deleted')
    application.register_method(toggle_premium, 'toggle_premium')
    application.register_method(toggle_draft, 'toggle_draft')
    application.register_method(regularize_keys, 'regularize_keys')
    application.register_method(premiumize_keys, 'premiumize_keys')
    application.register_method(publish_keys, 'publish_keys')
    application.register_method(draft_keys, 'draft_keys')
    application.register_method(toggle_keys_starred, 'toggle_keys_starred')
    application.register_method(toggle_keys_active, 'toggle_keys_active')
    application.register_method(activate_user_keys, 'activate_user_keys')
    application.register_method(deactivate_user_keys, 'deactivate_user_keys')
    application.register_method(get_person_from_user, 'get_person_from_user')
    application.register_method(get_users, 'get_users')
    application.register_method(get_articles, 'get_articles')
    application.register_method(get_article, 'get_article')
    application.register_method(save_article, 'save_article')
    application.register_method(get_article_content, 'get_article_content')
    application.register_method(get_books, 'get_books')
    application.register_method(get_book, 'get_book')
    application.register_method(save_book, 'save_book')
    application.register_method(is_openlibrary_cover_available, 'is_cover_available')
    application.register_method(get_training_programs, 'get_training_programs')
    application.register_method(get_training_program, 'get_training_program')
    application.register_method(save_training_program, 'save_training_program')


    run_wsgi_app(application)

if __name__ == '__main__':
	main()
