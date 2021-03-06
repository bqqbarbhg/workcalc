#!/usr/bin/env python

import csv
import sys
from datetime import datetime, timedelta
import itertools
import operator
import os

use_colors = sys.stdout.isatty()

if use_colors:
    try:
        import colorama
        if os.name == 'nt':
            colorama.init(strip=True, convert=True)
        else:
            colorama.init()
    except ImportError:
        print 'For colors install colorama      ($ pip install colorama)'
        use_colors = False

tformat = "%H:%M"

def parsetime(str):
    try:
        return datetime.strptime(str, tformat)
    except ValueError:
        return None

def abshourminute(td):
    hours, rem = divmod(td.seconds, 60**2)
    minutes, sec = divmod(rem, 60)
    hours += td.days * 24

    return hours, minutes

def hourminute(td):
    if td < timedelta():
        return abshourminute(-td), True
    else:
        return abshourminute(td), False

def formatahm(hm):
    return "%02d:%02d" % hm
def formathm(hm, pos=' ', neg='-'):
    return "%s%02d:%02d" % ((pos, neg)[hm[1]], hm[0][0], hm[0][1])

def formatd(td, *args):
    return formathm(hourminute(td), *args)

def grouped(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

workday = timedelta(hours=7, minutes=45)
lunchbonus = timedelta(minutes=30)

mapping = { }

total_time = timedelta()
expected_time = timedelta()

days = []

cur_time_raw = datetime.now()
cur_time = datetime(1900,1,1, hour=cur_time_raw.hour, minute=cur_time_raw.minute)

nulltime = (timedelta(), timedelta())
addtime = lambda x,y: tuple(map(operator.add, x, y))

zerotime = parsetime('0:00')

with open(sys.argv[1], 'rb') as csvfile:
    reader = csv.reader(csvfile)
    mapping = { n: i for (i, n) in enumerate(next(reader)) }

    for row in reader:
        getcol = lambda n: row[mapping[n]]
        gettimecol = lambda n: parsetime(getcol(n))

        start = gettimecol('Start')
        end = gettimecol('End')
        lunch = getcol('Lunch?') == 'Yes'
        adjust = gettimecol('Adjust')
        adjust_delta = adjust - zerotime if adjust else None

        if start and not end:
            end = cur_time

        if None in (start, end, lunch):
            days.append(nulltime)
            continue

        duration = end - start
        if not lunch:
            duration += lunchbonus
        if adjust_delta:
            duration -= adjust_delta

        total_time += duration
        expected_time += workday

        delta = duration - workday

        days.append((duration, delta))

weeks = list(grouped(days, 5, nulltime))
months = list(grouped(weeks, 4, []))

def isnull(td):
    return td.seconds == 0 and td.days == 0

def formattad(t, td):
    if use_colors:
        ts = ''
        ds = ((colorama.Fore.RED, colorama.Fore.GREEN)[td >= timedelta()] + 
            (colorama.Style.BRIGHT if abs(td) >= timedelta(minutes=30) else ''))
        ns = ''
        rs = colorama.Fore.RESET + colorama.Style.RESET_ALL
    else:
        ts = ds = ns = rs = ''

    if isnull(t) and isnull(td):
        return ns + ' ' + '.' * 12 + rs
    return "%s %s" % (ts + formatd(t), ds + formatd(td, '+')) + rs

total_sum = nulltime

print ''
for month in months:
    weeklist = []
    sumlist = []

    for week in month:
        weeklist.append([x if x else nulltime for x in week])
        sumlist.append(reduce(addtime, week, nulltime))

    weeklist_transposed = itertools.izip_longest(*weeklist, fillvalue=nulltime)
    msum = reduce(addtime, sumlist, nulltime)
    total_sum = addtime(total_sum, msum)

    ind = ' ' * 2
    sep = ' ' * 3
    print '\n'.join(ind + sep.join(formattad(*day) for day in week) for week in weeklist_transposed)
    print ''
    print ind + sep.join(formattad(*x) for x in sumlist)
    print ''
    print 'Month: %s' % formattad(*msum)
    print ''

print 'Total: %s' % formattad(*total_sum)

if use_colors:
    colorama.deinit()

