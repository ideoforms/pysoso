import re
import time
import urllib2
import urlparse
import feedparser
import lxml.html
import email.utils
import sqlite3
import xml.dom.minidom
import smtplib
import random
import string
from email.mime.text import MIMEText
from BeautifulSoup import BeautifulStoneSoup

def useragent_is_mobile(ua):
	mobile_agents = [
		"iPhone",
		"iPod",
		"Android",
		"dream",
		"CUPCAKE",
		"blackberry9500",
		"blackberry9530",
		"blackberry9520"
		"blackberry9550",
		"blackberry 9800",
		"webOS",
		"incognito",
		"webmate",
		"s8000",
		"bada"
	]
	
	for agent in mobile_agents:
		if re.search(agent, ua):
			return True

	return False

def send_email(text, you, me, subject):
	msg = MIMEText(text)
	msg['To'] = you
	msg['From'] = me
	msg['Subject'] = subject

	s = smtplib.SMTP("localhost")
	s.sendmail(me, [you], msg.as_string())
	s.quit()

def feed_modified(url, lastmod = 0, etag = None):
	""" given a feed URL and lastmod date in seconds since epoch (UTC),
		returns a new last-modified date """

	req = urllib2.Request(url)
	
	if lastmod:
		req.add_header("If-Modified-Since", date_to_rfc2822(lastmod))
	if etag:
		req.add_header("If-None-Match", etag)
	
	try:
		stamp = {}
		response = urllib2.urlopen(req, timeout = 10)
		headers = response.info()
		
		if 'xml' not in response.info()['content-type']:
			raise Exception, "Not a valid RSS document"

		stamp['etag'] = headers.get("etag")

		body = response.read()
		data = feedparser.parse(body)
		stamp['title'] = data.feed.title if data.feed.has_key("title") else ""
		stamp['link'] = data.feed.link if data.feed.has_key("link") else ""
		stamp['modified'] = None
		stamp['rebuilt'] = None

		lastmod = headers.get("Last-Modified")
		if lastmod:
			stamp['modified'] = stamp['rebuilt'] = date_from_rfc2822(lastmod)

		if data.feed.has_key('lastbuilddate'):
			stamp['modified'] = stamp['rebuilt'] = date_from_rfc2822(data.feed.lastbuilddate)

		if len(data.entries) > 0:
			if data.entries[0].has_key("updated_parsed"):
				stamp['modified'] = int(time.mktime(data.entries[0].updated_parsed))
				if not stamp.has_key('rebuilt'):
					stamp['rebuilt'] = stamp['modified']

		# what to do if the feed does not have a modified date?

		return stamp
	
	except Exception, e:
		print "feed parsing failed: %s" % e
		return {}

def feed_detect(url):
	feed_url = None
	try:
		f = urllib2.urlopen(url)
	except:
		return None

	if 'xml' in f.info()['content-type']:
		feed_url = url
	else:
		tree = lxml.html.fromstring(f.read())
		links = tree.xpath("//link[@type='application/rss+xml' or @type='application/atom+xml']")
		if links:
			feed_url = links[0].get('href')
			# fix relative paths
			feed_url = urlparse.urljoin(url, feed_url)

	return feed_url

def save_bookmark(db, user_id, bookmark):
	"""Store a bookmark."""
	c = db.cursor()
	feed_id = c.execute('select feed_id from feed where rss = ?', [ bookmark["rss"] ]).fetchone()

	if not bookmark.has_key("bookmark_id"):
		bookmark["bookmark_id"] = None

	if feed_id:
		bookmark["feed_id"] = feed_id[0]
	else:
		stamp = feed_modified(bookmark["rss"])
		if not stamp:
			raise Exception, "Invalid feed"

		c.execute('insert into feed (url, rss, added, rebuilt, modified, etag) values (?, ?, ?, ?, ?, ?)',
			(bookmark["url"], bookmark["rss"], int(time.time()), stamp['rebuilt'], stamp['modified'], stamp['etag']))
		bookmark["feed_id"] = c.lastrowid

	try:
		c.execute('insert or replace into bookmark (bookmark_id, user_id, feed_id, title, created, stale) values (?, ?, ?, ?, ?, ?)',
			(bookmark["bookmark_id"], user_id, bookmark["feed_id"], bookmark["title"], int(time.time()), False))
		bookmark["bookmark_id"] = c.lastrowid
		db.commit()

		db.execute("delete from tag where bookmark_id = ?", [ bookmark["bookmark_id"] ])
		for tag in bookmark['tags']:
			db.execute("insert into tag (bookmark_id, tag) values (?, ?)", [ bookmark["bookmark_id"], tag ])
		db.commit()

		return bookmark["bookmark_id"]

	except sqlite3.Error, e:
		print "An error occurred:", e.args[0]

def parse_opml(data):
	"""Parse an OPML document containing bookmarks, as exported by Rososo"""
	doc = xml.dom.minidom.parseString(data)

	bookmarks = []

	for node in doc.getElementsByTagName("outline"):
		if not node.attributes.has_key("htmlUrl"):
			continue
		category_node = node.parentNode
		category_name = category_node.attributes["title"].value if category_node.attributes else None
		# print " - parse: %s - %s" % (category_name, node.attributes["title"].value)
		bookmark = {
			"tags": [ category_name ] if category_name else [],
			"url": node.attributes["htmlUrl"].value,
			"rss": node.attributes["xmlUrl"].value,
			"title": node.attributes["title"].value
		}
		bookmark["title"] = unicode(BeautifulStoneSoup(bookmark["title"], convertEntities = BeautifulStoneSoup.HTML_ENTITIES))
		bookmarks.append(bookmark)

	return bookmarks

if __name__ == '__main__':
	main()

def url_sanify(url):
	url_parts = urlparse.urlsplit(url)
	if url_parts[0] == "":
		url = "http://%s" % url
	elif not (url_parts[0] == "http" or url_parts[0] == "https"):
		return None;

	return url
	
def date_to_rfc2822(seconds):
	""" takes timestamp in UTC, returns RFC2822-formatted string """
	return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(seconds))

def date_from_rfc2822(string):
	# return email.utils.parsedate_tz(string)
	return int(time.mktime(email.utils.parsedate(string)))

def date_ago():
   return 0

def generate_password(length = 10):
	"""Generate a random alphanumeric password."""
	chars = string.letters + string.digits
	password = "".join([ random.choice(chars) for n in range(length) ])
	return password

def recommendations_for_user(db, user_id = 1):
	"""generate feed recommendations based on a user-to-user similarity matrix.
	   similarity score represents the fraction of bookmarks that user A shares
	   with user B. the closest 3 users are selected, and new bookmarks picked
	   at random."""

	users = db.execute('select user_id, 1.0 * count(*) / max as score from bookmark, (select feed_id, (select count(*) as max from bookmark where user_id = ?) as max from bookmark where user_id = ? group by feed_id) as myfeeds where bookmark.feed_id = myfeeds.feed_id group by user_id having score > 0.02 order by score desc limit 3', [ user_id, user_id ])

	if users:
		user_ids = ", ".join(map(lambda n: str(n["user_id"]), users))
		feeds = db.execute('select feed.*, bookmark.feed_id, bookmark.title as title, sum(myfeeds.feed_id == bookmark.feed_id) as ex from bookmark, feed, (select feed_id from bookmark where user_id = ?) as myfeeds where user_id in (' + user_ids + ') and feed.feed_id = bookmark.feed_id group by bookmark.feed_id having ex = 0 order by random() limit 5', [ user_id ])
		return feeds
	else:
		return []

from logging import Handler, StreamHandler
from flask import request

class WSGILogHandler(StreamHandler):
	""" handy Logger handler which dispatches to the current VirtualHost's error_log """
	__init__ = Handler.__init__

	@property
	def stream(self):
		if request:
			return request.environ['wsgi.errors']
		return sys.stderr

