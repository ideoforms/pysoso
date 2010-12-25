#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
    pysoso
    ~~~~~~~~

    a lightweight replacement for rososo.

    :copyright: (c) 2010 by daniel jones
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import time

import psutil
import werkzeug
import urlparse
import sys
import os
import re

from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, jsonify, make_response
from werkzeug import check_password_hash, generate_password_hash


# configuration
# DATABASE = 'pysoso.db'
# DATABASE = '/var/www/vhosts/ideoforms.com/apps/pysoso/pysoso.db'
# DATABASE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "pysoso.db")
# DATABASE = '/var/www/vhosts/ideoforms.com/apps/pysoso/pysoso.db'
DATABASE = '/var/www/vhosts/ideoforms.com/apps/pysoso-dev/pysoso.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = g.db.execute('select user_id from user where username = ?',
                       [username]).fetchone()
    return rv[0] if rv else None

def process_bookmarks(bookmark_tags):
    bookmarks = []
    tags = []
    for bookmark in bookmark_tags:
        found = False
        for existing in bookmarks:
            if existing["rss"] == bookmark["rss"]:
                existing["tags"].append(bookmark["tag"])
                found = True
                break
        if not found:
            if bookmark["tag"]:
                bookmark["tags"] = [ bookmark["tag"] ]
            bookmarks.append(bookmark)
    return bookmarks

def get_bookmark(bookmark_id):
    bookmark_tags = query_db("select feed.*, bookmark.*, tag.tag from feed, bookmark left join tag on tag.bookmark_id = bookmark.bookmark_id where feed.feed_id = bookmark.feed_id and bookmark.bookmark_id = ? order by modified desc", [ bookmark_id ])
    return process_bookmarks(bookmark_tags)[0]

def get_bookmarks_for_user(user_id):
    bookmark_tags = query_db("select feed.*, bookmark.*, user.*, tag.tag from feed, bookmark, user left join tag on tag.bookmark_id = bookmark.bookmark_id where bookmark.user_id = user.user_id and feed.feed_id = bookmark.feed_id and user.user_id = ? order by modified desc", [ user_id ])
    return process_bookmarks(bookmark_tags)

def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

def format_timeago(timestamp):
    """Format a timestamp based on time elapsed since."""
    now = time.time()
    elapsed = time.time() - timestamp
    if elapsed > 31536000:
        years = int(elapsed / 31536000)
        return "%d %s ago" % (years, "year" if years == 1 else "years")
    elif elapsed > 604800:
        weeks = int(elapsed / 604800)
        return "%d %s ago" % (weeks, "week" if weeks == 1 else "weeks")
    elif elapsed > 86400:
        days = int(elapsed / 86400)
        return "%d %s ago" % (days, "day" if days == 1 else "days")
    elif elapsed > 3600:
        hours = int(elapsed / 3600)
        return "%d %s ago" % (hours, "hour" if hours == 1 else "hours")
    elif elapsed > 60:
        minutes = int(elapsed / 60)
        return "%d %s ago" % (minutes, "minute" if minutes == 1 else "minutes")
    elif elapsed > 10:
        seconds = int(elapsed)
        return "%d %s ago" % (seconds, "second" if seconds == 1 else "seconds")
    elif elapsed > 0:
        return "a few seconds ago"
    else:
        return "in the future"

@app.before_request
def before_request():
    """Make sure we are connected to the database each request and look
    up the current user so that we know he's there.
    """
    g.db = connect_db()
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)
        g.prefs = query_db('select * from prefs where user_id = ?',
                          [session['user_id']], one = True)
        if not g.prefs:
            g.prefs = {
                'new_window'   : True
            }
            g.db.execute("insert into prefs (user_id) values (?)", [ session["user_id"] ])
            g.db.commit()

    app.jinja_env.globals["is_mobile"] = psutil.useragent_is_mobile(request.user_agent.string)

@app.after_request
def after_request(response):
    """Closes the database again at the end of the request."""
    g.db.close()
    return response


@app.route('/')
def home():
    """show my bookmarks"""
    if not g.user:
        return redirect(url_for('login'))

    bookmarks = get_bookmarks_for_user(session["user_id"])
    stale = filter(lambda n: n["stale"], bookmarks)
    bookmarks = filter(lambda n: not n["stale"], bookmarks)

    # stale = query_db("select feed.*, bookmark.*, user.* from feed, bookmark, user where bookmark.user_id = user.user_id and bookmark.stale and feed.feed_id = bookmark.feed_id and user.user_id = ? order by modified desc", [ session['user_id'] ])

    tags = query_db("select tag from tag, bookmark, user where bookmark.user_id = user.user_id and tag.bookmark_id = bookmark.bookmark_id and user.user_id = ? group by tag", [ session['user_id'] ])
    tags = map(lambda n: n["tag"], tags)

    return render_template('home.html', bookmarks = bookmarks, stale = stale, tags = tags)

@app.route('/click/<int:bookmark_id>', methods = ['GET'])
def click(bookmark_id):
    """ Redirect to a link. """
    if 'user_id' not in session:
        abort(401)

    link = query_db("select feed.*, bookmark.* from bookmark, feed where bookmark.feed_id = feed.feed_id and bookmark_id = ?", [ bookmark_id ], one = True)
    if not link:
        error = "Could not find bookmark with ID %s" % bookmark_id
        return render_template('home.html', error = error)
    g.db.execute('update bookmark set stale = 1 where bookmark_id = ?', [ bookmark_id ])
    g.db.commit()

    return redirect(link["url"])

@app.route('/bookmark/lookup/', methods = ['GET', 'POST'])
def bookmark_lookup():
    """ Look up a feed based on this URL """
    if 'user_id' not in session:
        abort(401)

    if not request.values.has_key('url') or not request.values['url']:
        print "rendered"
        return render_template('bookmark/add.html')

    url = request.values['url']
    url_bits = urlparse.urlparse(url)
    url_host = url_bits[1].lstrip("www.")

    flask_base = url_for("home", _external = True)
    flask_base_bits = urlparse.urlparse(flask_base)
    flask_base_host = flask_base_bits[1].lstrip("www.")

    if (url_host == flask_base_host):
        return render_template('bookmark/add.html', error = "Sorry, I can't add myself as a feed.")

    url = psutil.url_sanify(url)

    feed = psutil.feed_detect(url)

    if not feed:
        return render_template('bookmark/add.html', error = "Sorry, I couldn't find an RSS feed for the URL <a href='%s'>%s</a>. Please verify that one exists." % (url, url))

    stamp = psutil.feed_modified(feed)
    if url == feed:
        url = stamp['link']

    bookmark = { 'url' : url, 'rss' : feed, 'title': stamp['title'], 'tags' : [] }

    return render_template('bookmark/save.html', bookmark = bookmark)

@app.route('/bookmark/save', methods=['POST'])
def bookmark_save():
    """Save a new bookmark."""
    if 'user_id' not in session:
        abort(401)

    if request.form['title']:
        bookmark = {
            'bookmark_id' : request.form['id'] if request.form['id'] else None,
            'rss' : request.form['rss'],
            'url' : request.form['url'],
            'title' : request.form['title'],
            'tags' : map(lambda n: n.rstrip(","), request.form['tags'].split())
        }
        feed_id = 0
        seen = []
        for tag in bookmark['tags']:
            if not re.search("^[a-zA-Z0-9_-]+$", tag):
                return render_template('bookmark/save.html', error = "Invalid tag: %s" % tag, bookmark = bookmark)
            if tag in seen:
                return render_template('bookmark/save.html', error = "Tag repeated: %s" % tag, bookmark = bookmark)
            seen.append(tag)

        try:
            bookmark_id = psutil.save_bookmark(g.db, session['user_id'], bookmark)

        except Exception, e:
            return render_template('bookmark/save.html', error = "Sorry, something went wrong whilst saving this bookmark. Please check that the feed URL is correct. (%s)" % e, bookmark = bookmark)

        # flash('Your message was recorded')
    return redirect(url_for('home'))

@app.route('/bookmark/delete/<bookmark_id>')
def bookmark_delete(bookmark_id):
    """Delete a bookmark."""
    if 'user_id' not in session:
        abort(401)

    link = query_db("select feed.*, bookmark.* from bookmark, feed where bookmark.feed_id = feed.feed_id and bookmark_id = ?", [ bookmark_id ], one = True)
    if not link:
        error = "Could not find bookmark with ID %s" % bookmark_id
        return render_template('home.html', error = error)
    g.db.execute('delete from bookmark where bookmark_id = ?', [ bookmark_id ])
    g.db.commit()

    return redirect(url_for('home'))


@app.route('/bookmark/edit/<int:bookmark_id>')
def bookmark_edit(bookmark_id):
    """Edit a bookmark."""
    if 'user_id' not in session:
        abort(401)

    bookmark = get_bookmark(bookmark_id)
    return render_template('bookmark/save.html', bookmark = bookmark)

@app.route('/bookmark/import', methods = ['GET', 'POST'])
def bookmark_import():
    """Import existing bookmarks in OPML format"""
    if 'user_id' not in session:
        abort(401)

    if request.method == 'GET':
        return render_template('bookmark/import.html')

    opml = request.files['file'].read()
    bookmarks = []
    error = None

    try:
        bookmarks = psutil.parse_opml(opml)
    except Exception, e:
        return render_template("bookmark/import.html", error = "Import failed, sorry! (%s)" % e)

    for bookmark in bookmarks:
        bookmark["imported"] = False
        try:
            psutil.save_bookmark(g.db, session["user_id"], bookmark)
            bookmark["imported"] = True
        except Exception, e:
            bookmark["exception"] = e

    bookmarks_imported = filter(lambda n: n["imported"], bookmarks)
    bookmarks_failed = filter(lambda n: not n["imported"], bookmarks)

    flash("Successfully imported %d bookmarks." % len(bookmarks_imported))

    return render_template('bookmark/import_done.html', bookmarks_imported = bookmarks_imported, bookmarks_failed = bookmarks_failed)

@app.route('/bookmark/export', methods = ['GET', 'POST'])
def bookmark_export():
    """Export existing bookmarks in OPML format"""
    if 'user_id' not in session:
        abort(401)

    if request.method == 'POST':
        bookmarks = query_db("select feed.*, bookmark.*, user.* from feed, bookmark, user where bookmark.user_id = user.user_id and feed.feed_id = bookmark.feed_id and user.user_id = ? order by modified desc", [ session['user_id'] ])
        response = make_response(render_template('bookmark/export.xml', bookmarks = bookmarks))
        response.headers["Content-Type"] = "application/xml"
        return response
    else:
        return render_template('bookmark/export.html')

@app.route('/bookmark/mark/<int:value>')
def mark(value):
    """Mark all bookmarks as fresh or stale"""
    if 'user_id' not in session:
        abort(401)

    if (value == 0 or value == 1):
        g.db.execute('update bookmark set stale = ? where user_id = ?', [ value, session['user_id'] ])
        g.db.commit()
        flash("bookmarks updated successfully.")
        
    return redirect(url_for('home'))

@app.route('/pref/<key>/<int:value>')
def pref(key, value):
    """Set user preference."""
    if 'user_id' not in session:
        abort(401)

    if not g.prefs.has_key(key):
        return render_template('home.html', error = "No such preference: %s" % key)

    g.db.execute('update prefs set new_window = ? where user_id = ?', [ value, session['user_id'] ])
    g.db.commit()
    flash("Preferences updated.")
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('home'))
    error = None

    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None or not check_password_hash(user['pw_hash'], request.form['password']):
            error = 'Invalid credentials. Please check your username and password and try again.'
        else:
            flash('You were logged in.')
            session['user_id'] = user['user_id']
            session.permanent = True
            return redirect(url_for('home'))

    return render_template('login.html', error = error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif re.search("[^a-zA-Z0-9_-]", request.form['username']) or len(request.form['username']) > 15:
            error = 'Invalid username. Usernames must be under 16 character, and contain only alphanumeric characters, underscore and hyphen.'
        elif not request.form['email'] or \
                 '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            c = g.db.cursor()
            c.execute('''insert into user (
                username, email, pw_hash) values (?, ?, ?)''',
                [request.form['username'], request.form['email'],
                 generate_password_hash(request.form['password'])])

            session['user_id'] = c.lastrowid

            g.db.commit()

            g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one = True)

            flash("thanks, you were registered successfully.")
            return render_template('welcome.html')

    return render_template('register.html', error=error)

@app.route('/lost', methods = ['GET', 'POST'])
def lost():
    """Sends out a lost password reminder."""
    if g.user:
        return redirect(url_for('home'))

    if request.method == 'GET' or not request.form['username']:
        return render_template("lost.html")
    else:
        user = query_db('select * from user where username = ?',
             [ request.form['username'] ], one = True)
        if not user:
            return render_template("lost.html", error = "sorry, couldn't find that username.")

        password = psutil.generate_password()
        hash = generate_password_hash(password)

        g.db.execute("update user set pw_hash = ? where user_id = ?", [ hash, user["user_id"] ])
        g.db.commit()

        email = render_template("lost-email.txt", user = user, password = password)
        psutil.send_email(email, user["email"], 'pysoso@ideoforms.com', "pysoso: lost password")

        flash("a new password has been sent out. it should be with you within a few minutes.")
        return render_template("lost.html")

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out.')
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/_add')
def add():
    return render_template('add.html')

@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)

# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['timeagoformat'] = format_timeago


if __name__ == '__main__':
    app.run(host="0.0.0.0")
