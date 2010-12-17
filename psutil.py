import time
import urllib2
import urlparse
import feedparser
import lxml.html
import email.utils
import sqlite3

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
        response = urllib2.urlopen(req)
        headers = response.info()
        
        stamp['etag'] = headers.get("etag")

        body = response.read()
        data = feedparser.parse(body)
        print "parsing body [%s]: %s" % (url, data.feed.keys())
        stamp['title'] = data.feed.title
        stamp['link'] = data.feed.link
        stamp['modified'] = None
        stamp['rebuilt'] = None

        lastmod = headers.get("Last-Modified")
        if lastmod:
            stamp['modified'] = stamp['rebuilt'] = date_from_rfc2822(lastmod)

        if data.feed.has_key('lastbuilddate'):
            stamp['rebuilt'] = date_from_rfc2822(data.feed.lastbuilddate)
            print "found last build date: %s -> %s" % (data.feed.lastbuilddate, stamp['rebuilt'])

        if len(data.entries) > 0:
            print "got %d posts" % len(data.entries)
            # print "0th: %s" % data.entries[0]
            if data.entries[0].has_key("updated_parsed"):
                stamp['modified'] = int(time.mktime(data.entries[0].updated_parsed))
                if not stamp.has_key('rebuilt'):
                    stamp['rebuilt'] = stamp['modified']

        return stamp
    
    except Exception, e:
        print e
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

def feed_bookmark(db, user_id, feed_url, feed_rss, feed_title):
    c = db.cursor()
    feed_id = c.execute('select feed_id from feed where rss = ?', [ feed_rss ]).fetchone()
    if not feed_id:
        stamp = feed_modified(feed_rss)
        c.execute('insert into feed (url, rss, added, rebuilt, modified, etag) values (?, ?, ?, ?, ?, ?)',
            (feed_url, feed_rss, int(time.time()), stamp['rebuilt'], stamp['modified'], stamp['etag']))
        feed_id = c.lastrowid
        print "(created) id: %s" % feed_id

    try:
        c.execute('insert into bookmark (user_id, feed_id, title, created, stale) values (?, ?, ?, ?, ?)',
            (user_id, feed_id, feed_title, int(time.time()), True))
        db.commit()
    except sqlite3.Error, e:
        print "An error occurred:", e.args[0]

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
