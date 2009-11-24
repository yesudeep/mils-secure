#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
import logging
from google.appengine.api import users, memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import render_template, dec
import utils
import models

logging.basicConfig(level=logging.DEBUG)


class IndexHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        username = user.nickname()

        cache_key = 'admin page ' + username
        cached_response = memcache.get(cache_key)
        if cached_response:
            self.response.out.write(cached_response)
        else:
            if '@' in username:
                username = username[:username.find('@')]
            response = render_template('admin/index.html',
                page_name='dashboard',
                username=username,
                blog_year_list=models.BLOG_YEAR_LIST,
                month_list=models.MONTH_LIST,
                logout_url=users.create_logout_url('/'))
            memcache.set(cache_key, response, utils.STATIC_PAGE_CACHE_TIMEOUT)
            self.response.out.write(response)

class UsersHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/generic_list.html', approved_user_count=models.User.get_approved_user_count(),
            user_count=models.User.get_user_count(), 
            deleted_user_count=models.User.get_deleted_user_count(),
            page_name='users', 
            page_description='Approving, editing, and sending messages to users is easy.  Just click on a name to perform any of these operations.')
        self.response.out.write(response)

class ArticlesHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/generic_list.html', page_name='articles', page_description='Add, remove, update articles and publish them.')
        self.response.out.write(response)

class BooksHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/generic_list.html', page_name='books', page_description='Add or remove books.')
        self.response.out.write(response)

class AnnouncementsHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/generic_list.html', page_name='announcements', page_description='Create new announcements to send to everyone in the list of users.')
        self.response.out.write(response)

class MailHandler(webapp.RequestHandler):
    def get(self):
        response = render_template('admin/generic_list.html', page_name='mails', page_description='Send mail to people')
        self.response.out.write(response)

class LogoutHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/admin'))

urls = [
	('/admin/?', UsersHandler),
	('/admin/mails/?', MailHandler),
    ('/admin/users/?', UsersHandler),
    ('/admin/books/?', BooksHandler),
    ('/admin/articles/?', ArticlesHandler),
    ('/admin/announcements/?', AnnouncementsHandler),
    ('/admin/logout/?', LogoutHandler),
]
application = webapp.WSGIApplication(urls, debug=config.DEBUG)

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
	main()

