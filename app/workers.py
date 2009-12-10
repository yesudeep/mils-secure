#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
import logging
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.api import urlfetch, mail, memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import apiproxy_errors
from utils import dec, render_template, queue_mail_task
import models
from datetime import datetime
from models import TrainingProgram, TrainingProgramFee, TrainingProgramRegistrant

logging.basicConfig(level=logging.DEBUG)

MAIL_SENDER = config.MAIL_SENDER
ADMIN_MAIL_SENDER = config.ADMIN_MAIL_SENDER

# Workers should be idempotent.  Very rare duplicate emails are OK.
# We can manage idempotence to a fair degree with memcache.

class MailComposeWorker(webapp.RequestHandler):
    def post(self):
        mail_key = self.request.get('mail_key')
        mail_object = db.get(db.Key(mail_key))
        email = self.request.get('email')

        sender = ADMIN_MAIL_SENDER
        cache_key = 'MailComposeWorker' + email + mail_key
        logging.info(cache_key)
        if not memcache.get(cache_key):
            mail.send_mail(sender=sender,
                to=email,
                subject=mail_object.subject,
                body=mail_object.body)
            logging.info('/worker/mail/compose/ subject: ' + mail_object.subject + ' sent to ' + email + ' from ' + sender )
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class SignupNotificationWorker(webapp.RequestHandler):
    def get(self, user_key):
        sender = MAIL_SENDER
        cache_key = 'SignupNotificationWorker' + user_key
        logging.info(cache_key)
        if not memcache.get(cache_key):
            user = db.get(db.Key(user_key))
            subject = '[MILS Alumni] Account Signup Notification'
            body = render_template('email/thank_you_for_registering.text', nickname=user.nickname)
            mail.send_mail(sender=sender,
                #to=[user.email, user.corporate_email],
                to=user.email,
                bcc=ADMIN_MAIL_SENDER,
                subject=subject,
                body=body)
            logging.info('/worker/mail/signup_notification/ sent to ' + user.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class AccountActivationNotificationWorker(webapp.RequestHandler):
    def get(self, user_key):
        sender = MAIL_SENDER
        cache_key = 'AccountActivationNotificationWorker' + user_key
        if not memcache.get(cache_key):
            user = db.get(db.Key(user_key))
            subject = '[MILS Alumni] Your account has been activated.'
            body = render_template('email/account_activation_notification.text', nickname=user.nickname)
            mail.send_mail(sender=sender,
                #to=[user.email, user.corporate_email],
                to=user.email,
                subject=subject,
                body=body)
            logging.info('/worker/mail/account_activation_notification/ sent to ' + user.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TrainingAnnouncementNotificationWorker(webapp.RequestHandler):
    def get(self, user_key):
        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementNotificationWorker' + user_key
        if not memcache.get(cache_key):
            user = db.get(db.Key(user_key))
            subject = '[MILS Alumni] Training announcement'
            body = render_template('email/training_announcement_notification.text', nickname=user.nickname)
            mail.send_mail(sender=sender,
                to=user.email,
                subject=subject,
                body=body)
            logging.info('/worker/mail/training_announcement_notification/ sent to ' + user.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TrainingAnnouncementCanceledNotificationWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementCanceledNotificationWorker.training_program.' + training_program_key + '.registrant.' + registrant_key
        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))

            subject = '[MILS Alumni] Training announcement canceled'
            body = render_template('email/training_announcement_canceled_notification.text', training_announcement=training_program, registrant=registrant)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)

            logging.info('/worker/mail/training_announcement_canceled_notification/ sent to ' + registrant.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TrainingAnnouncementRegistrationNotificationWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementRegistrationNotificationWorker.' + training_program_key + registrant_key

        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))
            subject = '[MILS Alumni] Thank you for registering for the training event'
            body = render_template('email/training_announcement_registration_notification.text',
                nickname=registrant.full_name,
                unregister_url= config.ROOT_URL + 'training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/unregister/',
                training_program_title=training_program.title)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)
            logging.info('/worker/mail/training_announcement_registration_notification/ sent to ' + registrant.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TrainingAnnouncementPaymentNotificationWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementPaymentNotificationWorker.' + training_program_key + registrant_key

        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))
            subject = '[MILS Alumni] Details for payment for the event'
            body = render_template('email/training_announcement_payment_notification.text',
                nickname=registrant.full_name,
                payment_details=config.PAYMENT_DETAILS,
                unregister_url= config.ROOT_URL + 'training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/unregister/',
                training_program_title=training_program.title)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)
            logging.info('/worker/mail/training_announcement_payment_notification/ sent to ' + registrant.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TrainingAnnouncementConfirmPaymentNotificationWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementConfirmPaymentNotificationWorker.' + training_program_key + registrant_key

        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))
            subject = '[MILS Alumni] Thank you for your payment for the event.'
            body = render_template('email/training_announcement_confirm_payment_notification.text',
                nickname=registrant.full_name,
                unregister_url= config.ROOT_URL + 'training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/unregister/',
                training_program_title=training_program.title)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)
            logging.info('/worker/mail/training_announcement_confirm_payment_notification/ sent to ' + registrant.email + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')


class TrainingAnnouncementUnregisterNotificationWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementUnregisterNotificationWorker.' + training_program_key + registrant_key

        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))

            subject = '[MILS Alumni] You have successfully unregistered from the event.'
            body = render_template('email/training_announcement_unregister_notification.text',
                nickname=registrant.full_name,
                renew_url= config.ROOT_URL + 'training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/register/',
                training_program_title=training_program.title)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)

            logging.info('/worker/mail/training_announcement_unregister_notification/ sent to ' + registrant.email + ' from ' + sender)

            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')


class BookOrderNotificationWorker(webapp.RequestHandler):
    def post(self):
        to = config.BOOK_VENDOR_EMAIL
        user_key = self.request.get('user_key')
        books = self.request.get('books')
        person_name = self.request.get('person_name')
        person_email_address = self.request.get('person_email_address')
        person_phone_number = self.request.get('person_phone_number')

        cache_key = 'BookOrderNotificationWorker' + user_key + books
        sender = MAIL_SENDER
        if not memcache.get(cache_key):
            user = db.get(db.Key(user_key))
            subject = '[MILS Alumni] ' + person_name + ' has placed a book order'
            body = render_template('email/book_order_notification.text',
                books=books,
                person_name=person_name,
                person_phone_number=person_phone_number,
                person_email_address=person_email_address,
                vendor_name=config.BOOK_VENDOR_NAME,
                vendor_phone_number=config.BOOK_VENDOR_PHONE_NUMBER,
                vendor_email_address=config.BOOK_VENDOR_EMAIL)
            mail.send_mail(sender=sender,
                to=config.BOOK_VENDOR_EMAIL,
                cc=person_email_address,
                bcc=config.ADMIN_EMAIL,
                subject=subject,
                body=body)
            logging.info('/worker/mail/book_order_notification/ sent to ' + config.BOOK_VENDOR_EMAIL + ' from ' + sender)
            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

class TaskCloseTrainingAnnouncementsWorker(webapp.RequestHandler):
    def get(self):
        today = datetime.utcnow()
        training_programs = TrainingProgram.get_all_closable_for_date(today.year, today.month, today.day)
        for training_program in training_programs:
            if not training_program.is_registration_closed:
#                fees = training_program.get_fees_sorted()
#                count = training_program.get_participant_count()
#                current_fee = max([f.fee for f in fees])
#                for fee in fees:
#                    if count <= fee.for_participant_count:
#                        current_fee = fee.fee
#                    else:
#                        continue
                for registrant in training_program.registrants:
                    queue_mail_task(url='/worker/mail/training_announcement/closure/',
                        params=dict(
                            registrant_key=str(registrant.key()),
                            training_program_key=str(training_program.key())
                        ),
                        method='POST'
                    )
                training_program.is_registration_closed = True
                training_program.put()

class TaskCalculatePaymentsForTrainingAnnouncementsWorker(webapp.RequestHandler):
    def get(self):
        today = datetime.utcnow()
        training_programs = TrainingProgram.get_all_payable_for_date(today.year, today.month, today.day)
        for training_program in training_programs:
#            if not training_program.is_registration_closed:
            fees = training_program.get_fees_sorted()
            count = training_program.get_participant_count()

            current_fee = max([f.fee for f in fees])
            for fee in fees:
                if count <= fee.for_participant_count:
                    current_fee = fee.fee
                else:
                    continue
            training_program.final_price = current_fee
            training_program.put()

            for registrant in training_program.registrants:
                queue_mail_task(url='/worker/mail/training_announcement_payment_notification/',
                    params=dict(
                        registrant_key=str(registrant.key()),
                        training_program_key=str(training_program.key()),
                        current_fee=current_fee
                    ),
                    method='POST'
                )

class TrainingAnnouncementClosureWorker(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        sender = MAIL_SENDER
        cache_key = 'TrainingAnnouncementClosureWorker.' + training_program_key + registrant_key

        if not memcache.get(cache_key):
            training_program = db.get(db.Key(training_program_key))
            registrant = db.get(db.Key(registrant_key))

            subject = '[MILS Alumni] Registrations for the ' + training_program.title + ' are complete.'
            body = render_template('email/training_announcement_registrations_closed.text',
                nickname=registrant.full_name,
                training_program=training_program)

            mail.send_mail(sender=sender,
                to=registrant.email,
                subject=subject,
                body=body)

            logging.info('/worker/mail/training_announcement/closure/ sent to ' + registrant.email + ' from ' + sender)

            memcache.set(cache_key, True, 120)
            self.response.out.write('not memcached + sent')
        self.response.out.write('memcached + not sending again')

urls = [
    ('/worker/mail/signup_notification/(.*)/?', SignupNotificationWorker),
    ('/worker/mail/account_activation_notification/(.*)/?', AccountActivationNotificationWorker),
    ('/worker/mail/book_order/?', BookOrderNotificationWorker),
    ('/worker/mail/compose/?', MailComposeWorker),
    ('/worker/mail/training_announcement_notification/(.*)/?', TrainingAnnouncementNotificationWorker),
    ('/worker/mail/training_announcement_registration_notification/?', TrainingAnnouncementRegistrationNotificationWorker),
    ('/worker/mail/training_announcement_payment_notification/?', TrainingAnnouncementPaymentNotificationWorker),
    ('/worker/mail/training_announcement_confirm_payment_notification/?', TrainingAnnouncementConfirmPaymentNotificationWorker),
    ('/worker/mail/training_announcement_unregister_notification/?', TrainingAnnouncementUnregisterNotificationWorker),
    ('/worker/mail/training_announcement/closure/?', TrainingAnnouncementClosureWorker),
    ('/worker/mail/training_announcement_canceled_notification/?', TrainingAnnouncementCanceledNotificationWorker),
    ('/worker/task/training_announcements/payments/calculate/?', TaskCalculatePaymentsForTrainingAnnouncementsWorker),
    ('/worker/task/training_announcements/close/?', TaskCloseTrainingAnnouncementsWorker),
]
application = webapp.WSGIApplication(urls, debug=config.DEBUG)

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
    main()

