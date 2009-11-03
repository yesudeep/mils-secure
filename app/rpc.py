#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
from google.appengine.api import users, memcache
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from lovely.jsonrpc import wsgi
from models import User, Person, Book, Article, TrainingProgram
from utils import dec
from django.utils import simplejson as json

MAX_FETCH_LIMIT = 400

rpc_methods = []

def rpc(f):
    rpc_methods.append((f, f.func_name))
    return f

@rpc
def get_user_names():
    users = User.all().order('nickname').fetch(MAX_FETCH_LIMIT)
    user_list = []
    for user in users:
        #person = user.people_singleton[0]
        user_list.append(user.to_json_dict('nickname', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
    return user_list

@rpc
def get_article_titles():
    articles = Article.all().order('title').fetch(MAX_FETCH_LIMIT)
    article_list = []
    for article in articles:
        article_list.append(article.to_json_dict('title', 'is_draft', 'when_published', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
    return article_list

@rpc
def get_book_titles():
    books = Book.all().order('title').fetch(MAX_FETCH_LIMIT)
    books_list = []
    for book in books:
        books_list.append(book.to_json_dict('title', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
    return books_list

@rpc
def get_announcement_titles():
    announcements = TrainingProgram.all().order('title').fetch(MAX_FETCH_LIMIT)
    announcements_list = []
    for announcement in announcements:
        announcements_list.append(announcement.to_json_dict('title', 'is_starred', 'is_active', 'is_deleted', 'when_created'))
    return announcements_list

@rpc
def get_user(key):
    user = db.get(db.Key(key))
    return user.to_json_dict(
        'username',
        'email',
        'nickname',
        'signin_email',
        'corporate_email',
        'identifier',
        'auth_provider',
        'wants_activation',
        'is_premium',
        'is_deleted',
        'is_active',
        'when_created'
    )


@rpc
def service_methods():
    return [n for m, n in rpc_methods]

def main():
    application = wsgi.WSGIJSONRPCApplication(json_impl=json)
    for method, method_name in rpc_methods:
        application.register_method(method, method_name)
    run_wsgi_app(application)

