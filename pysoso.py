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
DATABASE = '/var/www/vhosts/ideoforms.com/apps/pysoso/pysoso.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
# app.url_map.converters['default'] = werkzeug.routing.PathConverter
# app.url_map.converters['string'] = werkzeug.routing.PathConverter
# app.url_map.converters['any'] = werkzeug.routing.PathConverter


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
    else:
        return "a few seconds ago"

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

    if psutil.useragent_is_mobile(request.user_agent.string):
        app.jinja_env.globals["is_mobile"] = True

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
    bookmarks = query_db("select feed.*, bookmark.*, user.* from feed, bookmark, user where bookmark.user_id = user.user_id and not bookmark.stale and feed.feed_id = bookmark.feed_id and user.user_id = ? order by modified desc", [ session['user_id'] ])
    stale = query_db("select feed.*, bookmark.*, user.* from feed, bookmark, user where bookmark.user_id = user.user_id and bookmark.stale and feed.feed_id = bookmark.feed_id and user.user_id = ? order by modified desc", [ session['user_id'] ])

    return render_template('home.html', bookmarks = bookmarks, stale = stale)

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

    if request.method == "GET":
        return render_template('bookmark/add.html')
        
    url = request.form['url']

    if not url:
        return render_template('bookmark/add.html')

    url = psutil.url_sanify(url)

    feed = psutil.feed_detect(url)

    if not feed:
        return render_template('bookmark/add.html', error = "Sorry, I couldn't find an RSS feed for the URL <a href='%s'>%s</a>. Please verify that one exists." % (url, url))

    stamp = psutil.feed_modified(feed)
    if url == feed:
        url = stamp['link']

    return render_template('bookmark/save.html', feed_url = url, feed_rss = feed, feed_title = stamp['title'])

@app.route('/bookmark/save', methods=['POST'])
def bookmark_save():
    """Save a new bookmark."""
    if 'user_id' not in session:
        abort(401)
    if request.form['title']:
        feed_rss = request.form['rss']
        feed_url = request.form['url']
        feed_title = request.form['title']
        feed_id = 0

        print "saving with id %d" % session['user_id']
        try:
            psutil.feed_bookmark(g.db, session['user_id'], feed_url, feed_rss, feed_title)
        except:
            return render_template('bookmark/save.html', error = "Sorry, something went wrong whilst saving this bookmark. Please check that the feed URL is correct.", feed_rss = feed_rss, feed_url = feed_url, feed_title = feed_title)
            

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

    bookmark = query_db("select feed.*, bookmark.* from bookmark, feed where bookmark.feed_id = feed.feed_id and bookmark_id = ?", [ bookmark_id ], one = True)
    return render_template('bookmark/save.html', feed_url = bookmark["url"], feed_rss = bookmark["rss"], feed_title = bookmark["title"])

@app.route('/bookmark/import', methods = ['GET', 'POST'])
def bookmark_import():
    """Import existing bookmarks in OPML format"""
    if 'user_id' not in session:
        abort(401)

    if request.method == 'POST':
        opml = request.files['file'].read()
        error = ""
        try:
            bookmarks = psutil.parse_opml(opml)
            for bookmark in bookmarks:
                psutil.feed_bookmark(g.db, session["user_id"], bookmark["url"], bookmark["rss"], bookmark["title"])
            flash("Successfully imported %d bookmarks." % len(bookmarks))
            
        except Exception, e:
            error = "Import failed, sorry! (%s)" % e

        return render_template('home.html', error = error)
        
    else:
        return render_template('bookmark/import.html')

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
