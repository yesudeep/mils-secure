#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configuration as config
from atexit import register
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

def send_mail_template(cache_key, request, template_name, template_values, to, subject, subject_prefix=config.SUBJECT_PREFIX, sender=config.MAIL_SENDER, **kwargs):
    body = render_template(template_name, **template_values)
    subject = subject_prefix + " " + subject
    send_mail_once(cache_key, request, body, to, subject, sender, **kwargs)

def send_mail_once(cache_key, request, body, to, subject, sender=config.MAIL_SENDER, **kwargs):
    if kwargs.has_key("bcc"):
        additional_key_params = """bcc: \"%s\",""" % (kwargs.get("bcc"),)
    else:
        additional_key_params = ""
    key = """
        {
            worker: \"%s\",
            cache_key: \"%s\",
            subject: \"%s\",
            sent_to: \"%s\",
            sent_by: \"%s\",
            %s
            body: \"%s\",
        }
    """ % (request.path, cache_key, subject, to, sender, additional_key_params, body)
    logging.info('Attempting to send mail: \n' + key)
    logging.info(request)
    if not memcache.get(key):
        mail.send_mail(sender=sender,
            to=to,
            subject=subject,
            body=body,
            **kwargs)
        logging.info("Mail Worker: " + key)
        memcache.set(key, True, 120)
        logging.info('Sent mail.')
    else:
        logging.info('Mail sent before.  Not sending again.')


class SendComposedMail(webapp.RequestHandler):
    def post(self):
        mail_key = self.request.get('mail_key')
        mail_object = db.get(db.Key(mail_key))
        email = self.request.get("email")
        
        send_mail_once(cache_key=email + " " + mail_key,
                       request=self.request,
                       to=email,
                       subject=mail_object.subject,
                       body=mail_object.body)


class SignupNotifier(webapp.RequestHandler):
    def get(self, user_key):
        user = db.get(db.Key(user_key))
        template_values = dict(nickame=user.nickname)
        if user.corporate_email and (not user.corporate_email == user.email):
            to = [str(user.email), str(user.corporate_email)]
        else:
            to = user.email
        send_mail_template(cache_key=user_key,
            request=self.request,
            to=to,
            bcc=ADMIN_MAIL_SENDER,
            reply_to=ADMIN_MAIL_SENDER,
            subject="Your account needs activation.",
            template_name="email/thank_you_for_registering.text",
            template_values=template_values)


class AccountActivationNotifier(webapp.RequestHandler):
    def get(self, user_key):
        user = db.get(db.Key(user_key))
        template_values = dict(nickname=user.nickname)
        if user.corporate_email and (not user.corporate_email == user.email):
            to = [str(user.email), str(user.corporate_email)]
        else:
            to = user.email
        
        send_mail_template(cache_key=user_key,
            request=self.request,
            to=to,
            reply_to=ADMIN_MAIL_SENDER,
            bcc=ADMIN_MAIL_SENDER,
            subject="Your account is activated.",
            template_name="email/account_activation_notification.text",
            template_values=template_values)


class TrainingProgramNotifier(webapp.RequestHandler):
    def get(self, user_key):
        user = db.get(db.Key(user_key))
        training_program_key = self.request.get("training_program_key")
        training_program = db.get(db.Key(training_program_key))
        
        template_values = dict(
            nickname=user.nickname,
            training_program=training_program)
        
        # TODO: Check whether corporate email and the user email are the same.
        # We don't want to send TWO emails to the same email address.
        if user.corporate_email and (not user.corporate_email == user.email):
            to = [str(user.email), str(user.corporate_email)]
        else:
            to = user.email
        send_mail_template(cache_key=user_key,
                           request=self.request,
                           to=to,
                           subject="Training Program: " + training_program.title + " with " + training_program.faculty,
                           template_name="email/training_announcement_notification.text",
                           template_values=template_values)


class TrainingProgramCanceledNotifier(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get("training_program_key")
        registrant_key = self.request.get("registrant_key")
        training_program = db.get(db.Key(training_program_key))
        registrant = db.get(db.Key(registrant_key))

        template_values = {
            "training_program": training_program,
            "registrant": registrant
            }

        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key,
                           request=self.request,
                           to=registrant.email,
                           subject="Training program canceled.",
                           template_name="email/training_announcement_canceled_notification.text",
                           template_values=template_values)


class TrainingProgramRegistrationNotifier(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get("training_program_key")
        registrant_key = self.request.get("registrant_key")
        registrant = db.get(db.Key(registrant_key))
        training_program = db.get(db.Key(training_program_key))

        template_values = {
            "nickname": registrant.full_name,
            "unregister_url": config.ROOT_URL + "training_announcements/" + training_program_key + "/registrant/" + registrant_key + "/unregister/",
            "training_program_title": training_program.title,
            }

        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key,
            request=self.request,
            to=registrant.email,
            subject="Thank you for registering for the training event",
            template_name="email/training_announcement_registration_notification.text",
            template_values=template_values)


class TrainingProgramPaymentNotifier(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')
        current_fee = self.request.get("current_fee")

        registrant = db.get(db.Key(registrant_key))
        training_program = db.get(db.Key(training_program_key))

        template_values = {
            "nickname": registrant.full_name,
            "current_fee": current_fee,
            "payment_details": config.PAYMENT_DETAILS,
            "training_program_title": training_program.title,
            }

        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key + " fee " + current_fee,
            request=self.request,
            to=registrant.email,
            subject="Payment details for the training program.",
            template_name="email/training_announcement_payment_notification.text",
            template_values=template_values)


class TrainingProgramConfirmPaymentNotifier(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        registrant = db.get(db.Key(registrant_key))
        training_program = db.get(db.Key(training_program_key))

        template_values = {
            "nickname": registrant.full_name,
            "training_program_title": training_program.title,
            }

        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key,
            request=self.request,
            to=registrant.email,
            subject="Thank you for your payment toward the training program.",
            template_name="email/training_announcement_confirm_payment_notification.text",
            template_values=template_values)


class TrainingProgramUnregisterNotifier(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get('training_program_key')
        registrant_key = self.request.get('registrant_key')

        registrant = db.get(db.Key(registrant_key))
        training_program = db.get(db.Key(training_program_key))

        template_values = {
            "nickname": registrant.full_name,
            "training_program_title": training_program.title,
            "renew_url": config.ROOT_URL + 'training_announcements/' + training_program_key + '/registrant/' + registrant_key + '/register/',
            }

        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key,
            request=self.request,
            to=registrant.email,
            subject="You have unregistered from the training program.",
            template_name="email/training_announcement_unregister_notification.text",
            template_values=template_values)


class BookOrderNotifier(webapp.RequestHandler):
    def post(self):
        user_key = self.request.get("user_key")
        books = self.request.get("books")
        person_name = self.request.get("person_name")
        person_email_address = self.request.get("person_email_address")
        person_phone_number = self.request.get("person_phone_number")

        template_values = dict(books=books,
            person_name=person_name,
            person_phone_number=person_phone_number,
            person_email=person_email_address,
            vendor_name=config.BOOK_VENDOR_NAME,
            vendor_phone_number=config.BOOK_VENDOR_PHONE_NUMBER,
            vendor_email_address=config.BOOK_VENDOR_EMAIL
            )

        send_mail_template(cache_key="user: " + user_key + " books: " + books,
            request=self.request,
            to=config.BOOK_VENDOR_EMAIL,
            bcc=config.ADMIN_EMAIL,
            subject=person_name + " has placed a book order",
            template_name="email/book_order_notification.text",
            template_values=template_values)


class SorryTrainingProgramClosed(webapp.RequestHandler):
    def post(self):
        training_program_key = self.request.get("training_program_key")
        registrant_key = self.request.get("registrant_key")
        training_program = db.get(db.Key(training_program_key))
        registrant = db.get(db.Key(registrant_key))
        
        template_values = dict(
            nickname=registrant.full_name,
            training_program=training_program
            )
        
        send_mail_template(cache_key=training_program_key + " registrant " + registrant_key,
            request=self.request,
            to=registrant.email,
            subject="Registrations for the " + training_program.title + "are complete.",
            template_name="email/training_announcement_registrations_closed.text",
            template_values=template_values
            )


class CronCloseTrainingPrograms(webapp.RequestHandler):
    def get(self):
        today = datetime.utcnow()
        training_programs = TrainingProgram.get_all_closable_for_date(today.year, today.month, today.day)
        for training_program in training_programs:
            if not training_program.is_registration_closed:
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


class CronCalculatePaymentForTrainingPrograms(webapp.RequestHandler):
    def get(self):
        from fee_calculation import calculate_fee
        
        today = datetime.utcnow()
        training_programs = TrainingProgram.get_all_payable_for_date(today.year, today.month, today.day)
        for training_program in training_programs:
            fees = training_program.get_fees_sorted_by_count()
            count = training_program.get_participant_count()
            current_fee = calculate_fee(fees, count)

            logging.info("fees: " + str(fees) + " count: " + str(count) + " current_fee: " + str(current_fee))
            training_program.final_price = current_fee
            training_program.is_payment_mail_queued = True
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

urls = (
    ('/worker/mail/signup_notification/(.*)/?', SignupNotifier),
    ('/worker/mail/account_activation_notification/(.*)/?', AccountActivationNotifier),
    ('/worker/mail/book_order/?', BookOrderNotifier),
    ('/worker/mail/compose/?', SendComposedMail),
    
    ('/worker/mail/training_announcement_notification/(.*)/?', TrainingProgramNotifier),
    ('/worker/mail/training_announcement_registration_notification/?', TrainingProgramRegistrationNotifier),
    ('/worker/mail/training_announcement_payment_notification/?', TrainingProgramPaymentNotifier),
    ('/worker/mail/training_announcement_confirm_payment_notification/?', TrainingProgramConfirmPaymentNotifier),
    ('/worker/mail/training_announcement_unregister_notification/?', TrainingProgramUnregisterNotifier),

    ('/worker/mail/training_announcement/closure/?', SorryTrainingProgramClosed),
    ('/worker/mail/training_announcement_canceled_notification/?', TrainingProgramCanceledNotifier),
    
    ('/worker/task/training_announcements/payments/calculate/?', CronCalculatePaymentForTrainingPrograms),
    ('/worker/task/training_announcements/close/?', CronCloseTrainingPrograms),
)
application = webapp.WSGIApplication(urls, debug=config.DEBUG)

def main():
    from gaefy.db.datastore_cache import DatastoreCachingShim
    DatastoreCachingShim.Install()
    run_wsgi_app(application)
    DatastoreCachingShim.Uninstall()

if __name__ == '__main__':
    main()

