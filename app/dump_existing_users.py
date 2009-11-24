#!/usr/bin/env python
# -*- coding: utf-8 -*-

from existing_users import USERS
import sys
import csv

f = open(sys.argv[1], 'wt')

try:
    fieldnames = ( 'email',
                   'company',
                   'designation',
                   'enrollment_fee',
                   'first_name',
                   'graduation_year',
                   'last_name',
                   'nearest_railway_line',
                   'payment_mode',
                   'phone_number',
                   't_shirt_size',)
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    headers = {}
    for n in fieldnames:
        headers[n] = n
    #print headers
    writer.writerow(headers)
    for k, v in USERS.iteritems():
        d = dict(email=k)
        d.update(v)
        #print d
        writer.writerow(d)
finally:
    f.close()
