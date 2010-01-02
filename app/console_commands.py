from models import User
from existing_users import USERS
import sys
import csv

def get_not_registered_emails():
    users = User.all()
    reg_user_emails = []
    for u in users:
        reg_user_emails.extend([u.email, u.signin_email, u.corporate_email])
    meet_user_emails = [unicode(k) for k in USERS.keys()]
    not_registered_emails = set(meet_user_emails) - set(reg_user_emails)
    return not_registered_emails

def get_contact_info_not_registered():
    not_registered_emails = get_not_registered_emails()
    #not_registered_users = [USERS[email] for email in not_registered_emails]
    not_registered_users = []
    for email in not_registered_emails:
        d = {'email': email}
        d.update(USERS[email])
        not_registered_users.append(d)

    fieldnames = ['email','phone_number','first_name','last_name', 'designation', 'company', 'graduation_year', 'nearest_railway_line', 'enrollment_fee', 'payment_mode', 't_shirt_size']
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    headers = {}
    for n in fieldnames:
        headers[n] = n
    writer.writerow(headers)
    for u in not_registered_users:
        writer.writerow(u)

def list_all_people():
    users = User.all()
    user_list = []
    for user in users:
        d = user.to_json_dict()
        person = user.people_singleton[0]
        d.update(person.to_json_dict())
        user_list.append(d)
    fieldnames = user_list[0].keys()
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    headers = {}
    for n in fieldnames:
        headers[n] = n
    writer.writerow(headers)
    for u in user_list:
        writer.writerow(u)

