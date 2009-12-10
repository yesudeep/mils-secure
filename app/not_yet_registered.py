from models import User
from existing_users import USERS
import sys
import csv

def get_not_registered_emails():
    users = User.all()
    reg_user_emails = [u.email for u in users]
    meet_user_emails = [unicode(k) for k in USERS.keys()]
    not_registered_emails = set(meet_user_emails) - set(reg_user_emails)
    return not_registered_emails

def get_contact_info_not_registered():
    not_registered_emails = get_not_registered_emails()
    not_registered_users = [USERS[email] for email in not_registered_emails]

    fieldnames = ['phone_number','first_name','last_name', 'designation', 'company', 'graduation_year', 'nearest_railway_line', 'enrollment_fee', 'payment_mode', 't_shirt_size']
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    headers = {}
    for n in fieldnames:
        headers[n] = n
    writer.writerow(headers)
    for u in not_registered_users:
        writer.writerow(u)

