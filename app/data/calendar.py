# -*- coding: utf-8; mode: python; indent-tabs-mode: nil; tab-width: 4; -*-

from datetime import datetime


MONTH_NAMES = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
    ]
MONTH_SHORT_NAMES = [month_name[:3] for month_name in MONTH_NAMES]

WEEKDAY_NAMES = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    ]
WEEKDAY_SHORT_NAMES = [weekday_name[:3] for weekday_name in WEEKDAY_NAMES]

CURRENT_YEAR = datetime.today().year

YEARS = range(1900, CURRENT_YEAR+1)
