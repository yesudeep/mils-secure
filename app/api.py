#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration
from google.appengine.ext import db, webapp
from google.appengine.api import memcache, users
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import queue_mail_task, dec, parse_iso_datetime_string, split_emails
import logging
import models
from models import PHONE_TYPES, Article, User, Person, TrainingProgram, TrainingProgramRegistrant, Book, TrainingProgramFee, TrainingProgramBrochure, ARTICLE_SECTION_TYPES, Mail, MailReceiver
from datetime import datetime
from django.utils import simplejson as json
from decimal import Decimal
from gaefy.jinja2.code_loaders import FileSystemCodeLoader
from haggoo.template.jinja2 import render_generator

render_template = render_generator(loader=FileSystemCodeLoader, builtins=configuration.TEMPLATE_BUILTINS)


MAX_FETCH_LIMIT = 400

logging.basicConfig(level=logging.INFO)

class UserApproveHandler(webapp.RequestHandler):
    def get(self, key):
        user = db.get(db.Key(key))
        user.is_active = True
        user.wants_activation = False
        user.put()
        User.increment_approved_user_count()
        queue_mail_task(url='/worker/mail/account_activation_notification/' + key, method='GET')
        self.response.out.write(user.is_active)

class UserUnapproveHandler(webapp.RequestHandler):
    def get(self, key):
        user = db.get(db.Key(key))
        user.is_active = False
        user.put()
        User.decrement_approved_user_count()
        self.response.out.write(user.is_active)

class UserDeleteHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_deleted = True
        o.put()
        User.increment_deleted_user_count()
        self.response.out.write(o.is_deleted)

class UserUndeleteHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_deleted = False
        o.put()
        User.decrement_deleted_user_count()
        self.response.out.write(o.is_deleted)

class AnnouncementApproveHandler(webapp.RequestHandler):
    def get(self, key):
        announcement = db.get(db.Key(key))
        announcement.is_active = True
        announcement.put()

        users = User.all().filter('email IN', ['atul.gawand@gmail.com', 'yesudeep@gmail.com']).fetch(MAX_FETCH_LIMIT)
        for user in users:
            queue_mail_task(url='/worker/mail/training_announcement_notification/' + str(user.key()), method='GET')

        self.response.out.write(announcement.is_active)

class RegistrantApproveHandler(webapp.RequestHandler):
    def get(self, registrant_key, training_key):
        o = db.get(db.Key(registrant_key))
        #if not o.is_active:
        #    training_program.increment_participant_count()
        o.is_active = True
        o.put()
        self.response.out.write(o.is_active)

class RegistrantConfirmPaymentHandler(webapp.RequestHandler):
    def get(self, registrant_key, training_key):
        o = db.get(db.Key(registrant_key))
        #if not o.is_active:
        o.is_active = True
        o.is_payment_received = True
        training_program = db.get(db.Key(training_key))
        training_program.increment_participant_count()
        o.put()
        queue_mail_task(url='/worker/mail/training_announcement_confirm_payment_notification/',
                params=dict(
                    registrant_key=registrant_key,
                    training_program_key=training_key
                ),
                method='POST'
            )
        self.response.out.write(o.is_payment_received)

class RegistrantUnapproveHandler(webapp.RequestHandler):
    def get(self, registrant_key, training_key):
        o = db.get(db.Key(registrant_key))
        if o.is_active:
            training_program = db.get(db.Key(training_key))
            training_program.decrement_participant_count()
        o.is_active = False
        o.put()
        self.response.out.write(o.is_active)

class ApproveHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_active = True
        o.put()
        self.response.out.write(o.is_active)

class UnapproveHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_active = False
        o.put()
        self.response.out.write(o.is_active)

class DeleteHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_deleted = True
        o.put()
        self.response.out.write(o.is_deleted)

class UndeleteHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_deleted = False
        o.put()
        self.response.out.write(o.is_deleted)

class ToggleStarHandler(webapp.RequestHandler):
    def get(self, key):
        o = db.get(db.Key(key))
        o.is_starred = not o.is_starred
        o.put()
        self.response.out.write(o.is_starred)

class ArticleEditHandler(webapp.RequestHandler):
    def get(self, key):
        article = db.get(db.Key(key))

        response = render_template('admin/edit_article.html', article_key=key, article=article, section_types=ARTICLE_SECTION_TYPES)
        self.response.out.write(response)

    def post(self, key):
        from markdown2 import markdown
        article = db.get(db.Key(key))

        title = self.request.get('title')
        content = self.request.get('content')
        slug_title = self.request.get('slug_title')
        section_type = self.request.get('section_type')

        #user = users.get_current_user()

        article.title = title
        article.slug_title = slug_title
        article.content = content
        article.section_type = section_type
        #article.author = user
        article.content_html = markdown(content)
        article.put()

        self.response.out.write(article.to_json('title', 'section_type', 'is_draft', 'is_deleted', 'is_active', 'is_starred'))

class BookEditHandler(webapp.RequestHandler):
    def get(self, key):
        book = db.get(db.Key(key))

        response = render_template('admin/edit_book.html', book_key=key, book=book)
        self.response.out.write(response)

    def post(self, key):
        book = db.get(db.Key(key))
        book.title = self.request.get('title')
        book.info_url = self.request.get('info_url')
        book.authors = self.request.get('authors')
        book.isbn_10 = self.request.get('isbn_10')
        book.isbn_13 = self.request.get('isbn_13')
        book.put()

        self.response.out.write(book.to_json('title', 'authors', 'isbn_10', 'isbn_13', 'is_deleted', 'is_active', 'is_starred'))

class ArticleApproveHandler(webapp.RequestHandler):
    def get(self, key):
        article = db.get(db.Key(key))
        article.is_active = True
        article.when_published = datetime.utcnow()
        article.put()
        self.response.out.write(article.is_active)

class MailApproveHandler(webapp.RequestHandler):
    def get(self, key):
        mail = db.get(db.Key(key))

        today = datetime.utcnow()


        to_emails = mail.to_emails
        users = User.get_all_by_filter(mail.to_users)
        for user in users:
            to_emails.append(user.email)

        receivers = [MailReceiver(email=email, mail=mail) for email in set(to_emails)]
        db.put(receivers)

        for receiver in receivers:
            queue_mail_task(url='/worker/mail/compose/',
                params=dict(
                    mail_key=str(mail.key()),
                    email=receiver.email
                ),
                method='POST'
            )
        mail.when_sent = today
        mail.is_active = True
        mail.put()

class MailListHandler(webapp.RequestHandler):
    def get(self):
        mails = Mail.get_all()
        mails_list = []
        for mail in mails:
            mails_list.append(mail.to_json_dict('subject', 'is_starred', 'is_active', 'is_deleted', 'when_created', 'when_modified'))
        self.response.out.write(json.dumps(mails_list))


TO_USERS_CHOICES = [
    'all',
    'approved',
    'registered',
    'deleted',
    'none'
]

class MailEditHandler(webapp.RequestHandler):
    def get(self, key):
        mail = db.get(db.Key(key))
        response = render_template('admin/edit_mail.html', mail=mail, to_users_choices=TO_USERS_CHOICES)
        self.response.out.write(response)

    def post(self, key):
        mail = db.get(db.Key(key))

        to_users = self.request.get('to_users')
        to_emails = self.request.get('to')
        subject = self.request.get('subject')
        body = self.request.get('body')

        if not mail.is_active:
            mail.subject = subject
            mail.body = body
            mail.to_users = to_users
            mail.to_emails = split_emails(to_emails)
            mail.put()

        self.response.out.write(mail.to_json('subject', 'is_deleted', 'is_active', 'is_starred'))

class MailNewHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/new_mail.html', to_users_choices=TO_USERS_CHOICES)
        self.response.out.write(response)

    def post(self):
        to_users = self.request.get('to_users')
        to_emails = self.request.get('to')
        subject = self.request.get('subject')
        body = self.request.get('body')

        mail = Mail()
        mail.is_active = False
        mail.subject = subject
        mail.body = body
        mail.to_users = to_users
        mail.to_emails = split_emails(to_emails)
        mail.put()

        self.response.out.write(mail.to_json('subject', 'is_deleted', 'is_active', 'is_starred'))


class ArticleNewHandler(webapp.RequestHandler):
    def get(self):
        today = datetime.utcnow()
        response = render_template('admin/new_article.html', today=today, section_types=ARTICLE_SECTION_TYPES)
        self.response.out.write(response)

    def post(self):
        from markdown2 import markdown

        title = self.request.get('title')
        content = self.request.get('content')
        slug_title = self.request.get('slug_title')
        section_type = self.request.get('section_type')

        content_html = markdown(content)

        #user = users.get_current_user()

        article = Article()
        article.title = title
        article.slug_title = slug_title
        article.content = content
        article.section_type = section_type
        #article.author = user
        article.content_html = content_html
        article.is_draft = True
        article.put()

        self.response.out.write(article.to_json('title', 'section_type', 'is_draft', 'is_deleted', 'is_active', 'is_starred'))

class BookNewHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/new_book.html')
        self.response.out.write(response)

    def post(self):
        book = Book()
        book.title = self.request.get('title')
        book.info_url = self.request.get('info_url')
        book.authors = self.request.get('authors')
        book.isbn_10 = self.request.get('isbn_10')
        book.isbn_13 = self.request.get('isbn_13')
        book.put()

        self.response.out.write(book.to_json('title', 'authors', 'isbn_10', 'isbn_13', 'is_deleted', 'is_active', 'is_starred'))

class AnnouncementNewHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/new_announcement.html')
        self.response.out.write(response)

    def post(self):
        title = self.request.get('title')
        venue = self.request.get('venue')
        when_from = self.request.get('when_from')
        when_to = self.request.get('when_to')
        faculty = self.request.get('faculty')
        when_registration_ends = self.request.get('when_registration_ends')
        when_payment_is_calculated = self.request.get('when_payment_is_calculated')
        max_participants = self.request.get('max_participants')
        brochure_url = self.request.get('brochure_url')

        training_program = TrainingProgram()
        training_program.title = title
        training_program.venue = venue
        training_program.when_from = parse_iso_datetime_string(when_from)
        training_program.when_to = parse_iso_datetime_string(when_to)
        training_program.faculty = faculty
        training_program.when_registration_ends = parse_iso_datetime_string(when_registration_ends)
        training_program.when_payment_is_calculated = parse_iso_datetime_string(when_payment_is_calculated)
        training_program.max_participants = dec(max_participants)
        training_program.brochure_url = brochure_url
        training_program.put()

        fees1 = Decimal(self.request.get('fees_1'))
        fees2 = Decimal(self.request.get('fees_2'))
        fees3 = Decimal(self.request.get('fees_3'))
        participants1 = dec(self.request.get('participants_1'))
        participants2 = dec(self.request.get('participants_2'))
        participants3 = dec(self.request.get('participants_3'))

        fees_1 = TrainingProgramFee(fee=fees1, for_participant_count=participants1)
        fees_1.training_program = training_program
        fees_2 = TrainingProgramFee(fee=fees2, for_participant_count=participants2)
        fees_2.training_program = training_program
        fees_3 = TrainingProgramFee(fee=fees3, for_participant_count=participants3)
        fees_3.training_program = training_program

        db.put([fees_1, fees_2, fees_3])

        self.response.out.write(training_program.to_json('title', 'is_deleted', 'is_active', 'is_starred', 'when_created'))

class AnnouncementEditHandler(webapp.RequestHandler):
    def get(self, key):
        training_program = db.get(db.Key(key))
        registrants = db.Query(TrainingProgramRegistrant) \
            .filter('training_program =', training_program) \
            .order('when_created').fetch(MAX_FETCH_LIMIT)
        response = render_template('admin/edit_announcement.html', announcement=training_program, announcement_key=key, registrants=registrants)
        self.response.out.write(response)

    def post(self, key):
        training_program = db.get(db.Key(key))

        title = self.request.get('title')
        venue = self.request.get('venue')
        when_from = self.request.get('when_from')
        when_to = self.request.get('when_to')
        faculty = self.request.get('faculty')
        when_registration_ends = self.request.get('when_registration_ends')
        when_payment_is_calculated = self.request.get('when_payment_is_calculated')
        max_participants = self.request.get('max_participants')
        brochure_url = self.request.get('brochure_url')

        training_program.title = title
        training_program.venue = venue
        training_program.when_from = parse_iso_datetime_string(when_from)
        training_program.when_to = parse_iso_datetime_string(when_to)
        training_program.faculty = faculty
        training_program.when_registration_ends = parse_iso_datetime_string(when_registration_ends)
        training_program.when_payment_is_calculated = parse_iso_datetime_string(when_payment_is_calculated)
        training_program.max_participants = dec(max_participants)
        training_program.brochure_url = brochure_url

        fees1 = Decimal(self.request.get('fees_1'))
        fees2 = Decimal(self.request.get('fees_2'))
        fees3 = Decimal(self.request.get('fees_3'))
        participants1 = dec(self.request.get('participants_1'))
        participants2 = dec(self.request.get('participants_2'))
        participants3 = dec(self.request.get('participants_3'))

        fees = training_program.fees
        fees_1 = fees[0]
        fees_2 = fees[1]
        fees_3 = fees[2]

        fees_1.fee = fees1
        fees_1.for_participant_count = participants1
        fees_2.fee = fees2
        fees_2.for_participant_count = participants2
        fees_3.fee = fees3
        fees_3.for_participant_count = participants3

        db.put([training_program, fees_1, fees_2, fees_3])

        self.response.out.write(training_program.to_json('title', 'is_deleted', 'is_active', 'is_starred', 'when_created'))


class UserEditHandler(webapp.RequestHandler):
    def get(self, key):
        user = db.get(db.Key(key))
        person = user.people_singleton[0]

        person_birthdate = person.birthdate

        values = dict(
            #countries=models.COUNTRIES_LIST,
            month_list=models.MONTH_LIST,
            year_list=models.BIRTH_YEAR_LIST,
            phone_types=models.PHONE_TYPES,
            hint_questions=models.HINT_QUESTIONS_TUPLE_MAP,
            t_shirt_sizes=models.T_SHIRT_TYPES_TUPLE_MAP,
            gender_choices=models.GENDER_CHOICES,
            railway_lines=models.RAILWAY_LINES_TUPLE_MAP,
            mils_year_list=models.MILS_YEAR_LIST,
            birthdate_day=person_birthdate.day,
            birthdate_month=person_birthdate.month,
            birthdate_year=person_birthdate.year,
        )

        response = render_template('admin/edit_user.html', user_key=key, user=user, person=person, **values)
        self.response.out.write(response)

    def post(self, key):
        user = db.get(db.Key(key))
        person = user.people_singleton[0]

        person.first_name = self.request.get('first_name')
        person.last_name = self.request.get('last_name')
        user.nickname = ' '.join([person.first_name, person.last_name])
        user.email = self.request.get('email')

        corporate_email = self.request.get('corporate_email').strip()
        if corporate_email:
            user.corporate_email = corporate_email
        person.company = self.request.get('company')
        person.designation = self.request.get('designation')
        person.graduation_year = dec(self.request.get('graduation_year'))
        person.t_shirt_size = self.request.get('t_shirt_size')
        person.gender = self.request.get('gender')

        birthdate_day = dec(self.request.get('birthdate_day'))
        birthdate_month = dec(self.request.get('birthdate_month'))
        birthdate_year = dec(self.request.get('birthdate_year'))
        person.birthdate = datetime(birthdate_year, birthdate_month, birthdate_day).date()

        phone_count = dec(self.request.get('phone_count'))
        if phone_count:
            phones = []
            for i in xrange(phone_count):
                phone_key = self.request.get('phone_' + str(i + 1) + '_key')
                phone = db.get(db.Key(phone_key))
                phone.number = self.request.get('phone_' + str(i + 1))
                phones.append(phone)
            db.put(phones)

        is_student = self.request.get('is_student')
        if is_student == 'yes':
            person.is_student = True

        user.put()
        person.put()
        self.response.out.write(user.to_json('nickname', 'email', 'is_starred', 'is_deleted', 'is_active', 'is_premium'))

class UserMarkPremiumHandler(webapp.RequestHandler):
    def get(self, key):
        user = db.get(db.Key(key))
        user.is_premium = True
        user.put()

        self.response.out.write(user.to_json('nickname', 'email', 'is_starred', 'is_deleted', 'is_active', 'is_premium'))

class UserUnmarkPremiumHandler(webapp.RequestHandler):
    def get(self, key):
        user = db.get(db.Key(key))
        user.is_premium = False
        user.put()

        self.response.out.write(user.to_json('nickname', 'email', 'is_starred', 'is_deleted', 'is_active', 'is_premium'))

class UserListHandler(webapp.RequestHandler):
    def get(self):
        #cache_key = 'UserListHandler'
        #cached_response = memcache.get(cache_key)
        #if cached_response:
        #    self.response.out.write(cached_response)
        #else:
        #    users = User.all().order('nickname').fetch(MAX_FETCH_LIMIT)
        #    user_list = []
        #    for user in users:
        #        user_list.append(user.to_json_dict('nickname',
        #            'is_starred', 'is_active', 'is_deleted', 'when_created'))
        #    response = json.dumps(user_list)
        #    memcache.set(cache_key, response, 60)
        #    self.response.out.write(response)
        users = User.get_all()
        user_list = []
        for user in users:
            user_list.append(user.to_json_dict('nickname',
                'auth_provider', 'signin_email', 'is_starred',
                'is_active', 'is_deleted', 'when_created'))
        response = json.dumps(user_list)
        self.response.out.write(response)

class BookListHandler(webapp.RequestHandler):
    def get(self):
        #books = Book.all().order('title').fetch(MAX_FETCH_LIMIT)
        books = Book.get_all()
        books_list = []
        for book in books:
            books_list.append(book.to_json_dict('title', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
        self.response.out.write(json.dumps(books_list))

class ArticleListHandler(webapp.RequestHandler):
    def get(self):
        #articles = Article.all().order('title').fetch(MAX_FETCH_LIMIT)
        articles = Article.get_all()
        articles_list = []
        for article in articles:
            articles_list.append(article.to_json_dict('title', 'section_type', 'is_draft', 'when_published', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
        self.response.out.write(json.dumps(articles_list))

class AnnouncementListHandler(webapp.RequestHandler):
    def get(self):
        #announcements = TrainingProgram.all().order('title').fetch(MAX_FETCH_LIMIT)
        announcements = TrainingProgram.get_all()
        announcements_list = []
        for announcement in announcements:
            d = announcement.to_json_dict('title', 'is_starred', 'is_active', 'is_deleted', 'when_created', 'is_canceled')
            d['participant_count'] = announcement.participant_count
            d['total_participant_count'] = announcement.total_participant_count
            announcements_list.append(d)
        self.response.out.write(json.dumps(announcements_list))

class AnnouncementRegistrantsListHandler(webapp.RequestHandler):
    def get(self, key):
        training_program = db.get(db.Key(key))
        registrants = training_program.registrants
        registrants_list = []
        for registrant in registrants:
            registrants_list.append(registrant.to_json_dict('full_name', 'email', 'phone_number', 'is_active', 'company', 'designation'))
        self.response.out.write(json.dumps(registrants_list))

class AnnouncementUnapproveHandler(webapp.RequestHandler):
    def get(self, key):
        training_program = db.get(db.Key(key))
        training_program.is_canceled = True
        #training_program.is_active = False
        training_program.put()

        for registrant in training_program.registrants:
            queue_mail_task(url='/worker/mail/training_announcement_canceled_notification/',
                params=dict(
                    registrant_key=str(registrant.key()),
                    training_program_key=key
                ),
                method='POST'
            )
        self.response.out.write(training_program.is_active)

urls = [
    (r'/api/users/(.*)/delete/?', UserDeleteHandler),
    (r'/api/users/(.*)/undelete/?', UserUndeleteHandler),
    (r'/api/users/(.*)/approve/?', UserApproveHandler),
    (r'/api/users/(.*)/unapprove/?', UserUnapproveHandler),
    (r'/api/users/(.*)/toggle_star/?', ToggleStarHandler),
    (r'/api/users/(.*)/mark_premium/?', UserMarkPremiumHandler),
    (r'/api/users/(.*)/unmark_premium/?', UserUnmarkPremiumHandler),
    (r'/api/users/list/?', UserListHandler),

    (r'/api/books/(.*)/delete/?', DeleteHandler),
    (r'/api/books/(.*)/undelete/?', UndeleteHandler),
    (r'/api/books/(.*)/approve/?', ApproveHandler),
    (r'/api/books/(.*)/unapprove/?', UnapproveHandler),
    (r'/api/books/(.*)/toggle_star/?', ToggleStarHandler),
    (r'/api/books/list/?', BookListHandler),

    (r'/api/announcements/(.*)/delete/?', DeleteHandler),
    (r'/api/announcements/(.*)/undelete/?', UndeleteHandler),
    (r'/api/announcements/(.*)/approve/?', AnnouncementApproveHandler),
    (r'/api/announcements/(.*)/unapprove/?', AnnouncementUnapproveHandler),
    (r'/api/announcements/(.*)/toggle_star/?', ToggleStarHandler),
    (r'/api/announcements/list/?', AnnouncementListHandler),
    (r'/api/announcements/(.*)/registrants/?', AnnouncementRegistrantsListHandler),
    #(r'/api/announcements/(.*)/cancel/?', AnnouncementCancelHandler),

    (r'/api/articles/(.*)/delete/?', DeleteHandler),
    (r'/api/articles/(.*)/undelete/?', UndeleteHandler),
    (r'/api/articles/(.*)/approve/?', ArticleApproveHandler),
    (r'/api/articles/(.*)/unapprove/?', UnapproveHandler),
    (r'/api/articles/(.*)/toggle_star/?', ToggleStarHandler),
    (r'/api/articles/list/?', ArticleListHandler),
    (r'/api/articles/(.*)/edit/?', ArticleEditHandler),
    (r'/api/articles/new/?', ArticleNewHandler),

    (r'/api/mails/(.*)/delete/?', DeleteHandler),
    (r'/api/mails/(.*)/undelete/?', UndeleteHandler),
    (r'/api/mails/(.*)/approve/?', MailApproveHandler),
    (r'/api/mails/(.*)/toggle_star/?', ToggleStarHandler),
    (r'/api/mails/list/?', MailListHandler),
    (r'/api/mails/new/?', MailNewHandler),
    (r'/api/mails/(.*)/edit/?', MailEditHandler),

    (r'/api/users/(.*)/edit/?', UserEditHandler),
    (r'/api/books/(.*)/edit/?', BookEditHandler),
    (r'/api/announcements/(.*)/edit/?', AnnouncementEditHandler),
    (r'/api/books/new/?', BookNewHandler),
    (r'/api/announcements/new/?', AnnouncementNewHandler),

    (r'/api/registrants/(.*)/approve/(.*)/?', RegistrantApproveHandler),
    (r'/api/registrants/(.*)/confirm_payment/(.*)/?', RegistrantConfirmPaymentHandler),
    (r'/api/registrants/(.*)/unapprove/(.*)/?', RegistrantUnapproveHandler),
]

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    application = webapp.WSGIApplication(urls, debug=configuration.DEBUG)
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
    main()

