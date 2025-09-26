#!/usr/bin/env python3

import re
import datetime
import uuid

def chomp(line):
	if line.endswith('\n'):
		line = line[:-1]
	if line.endswith('\r'):
		line = line[:-1]

	return line

def sanitize(field):
	trans = { '\xa0': ' ', '\u2018': "'", '\u2019': "'" }

	field = field.strip()
	field = field.translate(str.maketrans(trans)).encode('ascii').decode()

	return field

class TsvReader:
	def __init__(self, stream):
		self._gen = self._gen(stream)
		self._head = next(self._gen)

	@staticmethod
	def _gen(stream):
		for line in stream:
			yield [ sanitize(field) for field in chomp(line).split('\t') ]

	def __iter__(self):
		for data in self._gen:
			assert len(data) == len(self._head)
			yield dict(zip( self._head, data ))

def parse_us_date(date):
	match = re.match(r'^(?P<B>\w+) (?P<d>\d+), (?P<y>\d+)$', date)
	m, d, y = match.groups()

	m = ( 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
		'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ).index( m[:3] ) + 1
	d, y = int(d), int(y)

	return datetime.date(y, m, d)

def ical_date(date):
	return date.strftime("%Y%m%d")

def ical_time(time):
	return time.strftime("%Y%m%dT%H%M%SZ")

if __name__ == '__main__':
	import sys

	args = sys.argv[1:]

	if len(args) >= 1 and args[0] == '-o':
		sys.stdout.close()
		sys.stdout = open(args[1], 'w')

		args = args[2:]

	if len(args) < 1:
		sys.stderr.write(f'Usage: { sys.argv[0] } [-o output.ics] input.tsv [...]' + '\n')
		sys.exit(1)

	user = 'anthakki'
	prog = 'bch_holidays'
	t_now = ical_time( datetime.datetime.utcnow() )

	print(f'BEGIN:VCALENDAR')
	print(f'VERSION:2.0')
	print(f'X-WR-CALNAME:{ "BCH holidays" }')
	print(f'PRODID:{ f"-//{ user }//{ prog }//EN" }')

	for arg in args:
		with open(arg, 'r') as stream:
			for line in TsvReader(stream):
				summary = line['Holiday']
				date_str, observed = re.match( r'^(.*?)((?:\s*[(][^)]*[)])?)$', line['Date'] ).groups()
				summary = summary + observed
				date = parse_us_date( date_str )

				d_beg = ical_date( date )
				d_end = ical_date( date + datetime.timedelta( days = 1 ) )

				url = f'https://github.com/{ user }/{ prog }/uid/{ d_beg }/{ summary }'
				uid = str(uuid.uuid5( uuid.NAMESPACE_URL, url )).upper()

				print(f'BEGIN:VEVENT')
				print(f'DTEND;VALUE=DATE:{ d_end }')
				print(f'DTSTAMP:{ t_now }')
				print(f'DTSTART;VALUE=DATE:{ d_beg }')
				print(f'SUMMARY:{ summary }')
				print(f'UID:{ uid }')
				print(f'END:VEVENT')

	print(f'END:VCALENDAR')
