#!/usr/bin/env python -U
# -*- coding: utf-8 -*-

import configuration as config
import logging
from google.appengine.api import memcache
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
import models
from data.existing_users import USERS
from utils import dec, queue_mail_task, render_template, AuthorizedRequestHandler
from django.utils import simplejson as json
from utils import get_iso_datetime_string
from models import TrainingProgram, TrainingProgramFee, Article, TrainingProgramRegistrant, Book
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

class IndexPage(AuthorizedRequestHandler):
    def get(self):
        if self.is_logged_in():
            self.redirect('/blog')
        cache_key = 'index_page'
        cached_html = memcache.get(cache_key)
        if cached_html:
            self.response.out.write(cached_html)
        else:
            response = render_template('index.html')
            memcache.set(cache_key, response, 120)
            self.response.out.write(response)

class UnsupportedBrowserPage(webapp.RequestHandler):
    def get(self):
        cache_key = 'unsupported_browser_page'
        cached_response = memcache.get(cache_key)
        if cached_response:
            self.response.out.write(cached_response)
        else:
            response = render_template('ie.html')
            memcache.set(cache_key, response, 10)
            self.response.out.write(response)


class BlogPage(AuthorizedRequestHandler):
    def get(self):
        auth_level = self.is_user_authorized()
        if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
            self.redirect('/account/activate/reminder/')
        elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            today = datetime.utcnow()

            year = self.request.get('year')
            month = self.request.get('month')

            if not year or not month:
                year = today.year
                month = today.month
            else:
                year = dec(year)
                month = dec(month)
            articles = Article.get_all_published_for_month(year, month)
            books = Book.get_latest(count=10)
            response = render_template('blog.html',
                year_list=models.BLOG_YEAR_LIST,
                month_list=models.MONTH_LIST,
                today=today,
                requested_year=year,
                requested_month=month,
                articles=articles,
                books=books)
            self.response.out.write(response)
        else:
            response = render_template('index.html')
            self.response.out.write(response)

class StudentsPage(AuthorizedRequestHandler):
    def get(self):
        auth_level = self.is_user_authorized()
        if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
            self.redirect('/account/activate/reminder/')
        elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            today = datetime.utcnow()

            year = self.request.get('year')
            month = self.request.get('month')

            if not year or not month:
                year = today.year
                month = today.month
            else:
                year = dec(year)
                month = dec(month)
            articles = Article.get_all_published_student_articles_for_month(year, month)
            books = Book.get_latest(count=10)
            response = render_template('blog_students.html',
                year_list=models.BLOG_YEAR_LIST,
                month_list=models.MONTH_LIST,
                today=today,
                requested_year=year,
                requested_month=month,
                articles=articles,
                books=books)
            self.response.out.write(response)
        else:
            response = render_template('index.html')
            self.response.out.write(response)


class PhotosPage(AuthorizedRequestHandler):
    def get(self):
        auth_level = self.is_user_authorized()
        if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
            self.redirect('/account/activate/reminder/')
        elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            self.redirect(config.PICASA_WEB_ALBUMS_PUBLIC_URL)

class AboutPage(AuthorizedRequestHandler):
    def get(self):
        #auth_level = self.is_user_authorized()
        #if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
        #    self.redirect('/account/activate/reminder/')
        #elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
        #    response = render_template('about.html')
        #    self.response.out.write(response)
        #else:
        #    response = render_template('index.html')
        #    self.response.out.write(response)
        response = render_template('about.html')
        self.response.out.write(response)

class JsonBlogHandler(AuthorizedRequestHandler):
    def get(self):
        year = self.request.get('year')
        month = self.request.get('month')
        #auth_level = self.is_user_authorized()
        #if auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            #self.redirect(config.PICASA_WEB_ALBUMS_PUBLIC_URL)
        articles = models.Article.get_all_published_for_month(dec(year), dec(month))
        articles_list = [
            dict(title=a.title,
            author_nickname=a.author.nickname(),
            author_email=a.author.email(),
            when_published=get_iso_datetime_string(a.when_published),
            content=a.html_content
            )
            for a in articles
        ]
        retval = json.dumps(articles_list)
        self.response.out.write(retval)

class JsonBooksHandler(AuthorizedRequestHandler):
    def get(self):
        books = models.Book.get_all_books()
        books_list = [
            dict(
                key=str(b.key()),
                title=b.title,
                authors=b.authors,
                isbn_10=b.isbn_10,
                isbn_13=b.isbn_13,
                info_url=b.info_url
            )
            for b in books
        ]
        retval = json.dumps(books_list)
        self.response.out.write(retval)

class BooksPurchaseHandler(AuthorizedRequestHandler):
    def post(self):
        session_user = self.get_session_user()
        keys = json.loads(self.request.get('keys'))

        user = models.User.get_user_from_identifier(session_user.identifier)
        orders = []
        books = []
        isbn_list = []
        for key in keys:
            book = db.get(db.Key(key))
            order = models.UserBookOrder(user=user, book=book)
            books.append(str(book))
            orders.append(order)
        db.put(orders)

        person = user.people_singleton[0]
        book_infos = '\n'.join(books)

        queue_mail_task(url='/worker/mail/book_order/',
            params=dict(
                user_key=str(user.key()),
                books=book_infos,
                person_name=str(person),
                person_email_address=user.email,
                person_phone_number = str(person.phones[0])
            ),
            method='POST'
        )
        self.response.out.write(json.dumps(keys))

class ExistingUserInfoHandler(webapp.RequestHandler):
    def get(self):
        from datetime import datetime
        email_address = self.request.get('email_address')
        corporate_email_address = self.request.get('corporate_email_address')
        existing_user = USERS.get(email_address, USERS.get(corporate_email_address, {
            'company': '',
            'designation': '',
            'enrollment_fee': 0,
            'first_name': '',
            'graduation_year': 0,
            'last_name': '',
            'nearest_railway_line': 'western',
            'payment_mode': '',
            'phone_number': '',
            't_shirt_size': 'medium',
        }))
        existing_user_json = json.dumps(existing_user)
        logging.info('[existing_user] ' + existing_user_json)
        self.response.out.write(existing_user_json)

class TrainingAnnouncementsPageHandler(AuthorizedRequestHandler):
    def get(self):
        auth_level = self.is_user_authorized()
        if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
            self.redirect('/account/activate/reminder/')
        elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            from datetime import datetime
            today = datetime.utcnow()

            training_announcements = TrainingProgram.get_all_approved_for_month(today.year, today.month)
            response = render_template('training_announcements.html', training_announcements=training_announcements)
            self.response.out.write(response)
        else:
            response = render_template('index.html')
            self.response.out.write(response)

class ArticleHandler(AuthorizedRequestHandler):
    def get(self, year, month, day, slug_title):
        year = dec(year)
        month = dec(month)
        day = dec(day)
        today = datetime.utcnow()
        articles = [Article.get_article_for_day_with_slug(year, month, day, slug_title)]
        logging.info(articles)
        response = render_template('blog.html',
            year_list=models.BLOG_YEAR_LIST,
            month_list=models.MONTH_LIST,
            current_year=today.year,
            current_month=today.month,
            articles=articles,
            show_comments=True)
        self.response.out.write(response)

        """auth_level = self.is_user_authorized()
        if auth_level == models.AUTH_LEVEL_REGISTERED_USER:
            self.redirect('/account/activate/reminder/')
        elif auth_level == models.AUTH_LEVEL_ACTIVATED_USER:
            year = dec(year)
            month = dec(month)
            day = dec(day)
            today = datetime.utcnow()
            articles = [Article.get_article_for_day_with_slug(year, month, day, slug_title)]
            logging.info(articles)
            response = render_template('blog.html',
                year_list=models.BLOG_YEAR_LIST,
                month_list=models.MONTH_LIST,
                current_year=today.year,
                current_month=today.month,
                articles=articles,
                show_comments=True)
            self.response.out.write(response)
        else:
            response = render_template('index.html')
            self.response.out.write(response)
        """
            
class TrainingAnnouncementRegistrationHandler(AuthorizedRequestHandler):
    def get(self, key):
        training_program = db.get(db.Key(key))
        session_user = self.get_session_user()
        user = models.User.get_user_from_identifier(session_user.identifier)
        person = user.people_singleton[0]
        phone_number = person.phones[0].number
        response = render_template('training_announcement_registration.html',
            training_announcement=training_program, user=user, phone_number=phone_number, person=person)
        self.response.out.write(response)

    def post(self, training_key):
        training_program = db.get(db.Key(training_key))
        nominations = dec(self.request.get('nominations_count'))

        #training_program.increment_participant_count(incr=nominations)
        training_program.increment_total_participant_count(incr=nominations)

        registrants = []
        for x in range(nominations):
            i = str(x + 1)
            full_name = self.request.get('full_name_' + i)
            phone_number = self.request.get('phone_number_' + i)
            email = self.request.get('email_' + i)
            company = self.request.get('company_' + i)
            designation = self.request.get('designation_' + i)
            registrant = TrainingProgramRegistrant()
            registrant.full_name = full_name
            registrant.phone_number = phone_number
            registrant.email = email
            # Let the admin determine who to activate.
            #registrant.is_active = True
            registrant.company = company
            registrant.designation = designation
            registrant.training_program = training_program
            registrants.append(registrant)
        db.put(registrants)

        if training_program.is_canceled:
            for registrant in registrants:
                registrant_key = str(registrant.key())
                queue_mail_task(url='/worker/mail/training_announcement_canceled_notification/',
                    params=dict(
                        registrant_key=registrant_key,
                        training_program_key=training_key
                    ),
                    method='POST'
                )
            response = render_template('training_announcement_canceled.html', training_announcement=training_program)
            self.response.out.write(response)
        else:
            for registrant in registrants:
                registrant_key = str(registrant.key())
                queue_mail_task(url='/worker/mail/training_announcement_registration_notification/',
                    params=dict(
                        registrant_key=registrant_key,
                        training_program_key=training_key
                    ),
                    method='POST'
                )
            self.redirect('/training_announcements/')

class TrainingAnnouncementsEmailAvailableHandler(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_announcement_key')
        index = self.request.get('index')
        email = self.request.get('email_' + index)
        training_program = db.get(db.Key(training_program_key))
        registrant = db.Query(TrainingProgramRegistrant).filter('training_program =', training_program) \
            .filter('email = ', email).get()
        logging.info(registrant)
        if registrant:
            response = False #"Email address is already registered.  Please choose another one."
        else:
            response = True
        logging.info(response)
        self.response.out.write(json.dumps(response))

class UnregisterRegistrantHandler(webapp.RequestHandler):
    def get(self, training_program_key, registrant_key):
        training_program = db.get(db.Key(training_program_key))
        response = render_template('unregister_registrant.html', training_announcement_key=training_program_key, registrant_key=registrant_key, training_announcement=training_program)
        self.response.out.write(response)

    def post(self, training_program_key, registrant_key):
        training_program = db.get(db.Key(training_program_key))
        registrant = db.get(db.Key(registrant_key))

        why_unregister = self.request.get('why_unregister')
        registrant.is_active = False
        registrant.why_unregister = why_unregister
        registrant.put()

        # Decrement the participant count only if the user was already active.
        if registrant.is_active:
            training_program.decrement_participant_count()

        queue_mail_task(url='/worker/mail/training_announcement_unregister_notification/',
            params=dict(
                registrant_key=registrant_key,
                training_program_key=training_program_key
            ),
            method='POST'
        )

        response = render_template('unregister_thanks.html', training_announcement=training_program)
        self.response.out.write(response)
        #self.redirect('/training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/unregister/thanks')

class RenewRegistrantHandler(webapp.RequestHandler):
    def get(self, training_program_key, registrant_key):
        training_program = db.get(db.Key(training_program_key))
        response = render_template('renew_registrant.html', training_announcement_key=training_program_key, registrant_key=registrant_key, training_announcement=training_program)
        self.response.out.write(response)

    def post(self, training_program_key, registrant_key):
        training_program = db.get(db.Key(training_program_key))

        registrant = db.get(db.Key(registrant_key))
        registrant.is_active = True
        registrant.put()

        training_program.increment_participant_count()

        queue_mail_task(url='/worker/mail/training_announcement_registration_notification/',
            params=dict(
                registrant_key=registrant_key,
                training_program_key=training_key
            ),
            method='POST'
        )
        self.redirect('/')

class ThankYouUnregisterHandler(AuthorizedRequestHandler):
    def get(self, training_program_key):
        training_program = db.get(db.Key(training_program_key))
        response = render_template('unregister_thanks.html', training_announcement=training_program)
        self.response.out.write(response)

urls = [
	('/', IndexPage),
	('/about/?', AboutPage),
    ('/article/([0-9]*)/([0-9]*)/([0-9]*)/(.*)/?', ArticleHandler),
	('/blog/?', BlogPage),
	('/students/?', StudentsPage),
	('/photos/?', PhotosPage),
	('/json/blog/?', JsonBlogHandler),
    ('/json/books/?', JsonBooksHandler),
    ('/json/books/buy/?', BooksPurchaseHandler),
    ('/json/existing_user/?', ExistingUserInfoHandler),
	('/announcement/(.*)/register/?', TrainingAnnouncementRegistrationHandler),
	('/training_announcements/?', TrainingAnnouncementsPageHandler),
	('/training_announcements/check_email_available/?', TrainingAnnouncementsEmailAvailableHandler),
    ('/training_announcements/(.*)/registrant/(.*)/unregister/?', UnregisterRegistrantHandler),
    ('/training_announcements/(.*)/registrant/(.*)/unregister/thanks/?', ThankYouUnregisterHandler),
    ('/unsupported/browser/?', UnsupportedBrowserPage),
	#('/privacy', PrivacyPage),
	#('/tos', TosPage),
	#('/help', HelpPage),
]
application = webapp.WSGIApplication(urls, debug=config.DEBUG)

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
	main()

