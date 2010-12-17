#!/usr/bin/python

import sys
import time
import pysoso
import psutil
import sqlite3

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "-q":
        sys.stdout = open('/dev/null', 'w')

    try:
        db = pysoso.connect_db()
        db.row_factory = sqlite3.Row
        rv = db.execute('select * from feed').fetchall()

        c = db.cursor()
        for entry in rv:
            print "%s" % entry['rss']
            stamp = psutil.feed_modified(entry['rss'], entry['modified'], entry['etag'])
            if stamp:
                print " - feed modified since last access"
                c.execute('update feed set modified = ?, etag = ? where feed_id = ?', (stamp['modified'], stamp['etag'], entry['feed_id']))
                if stamp['modified'] > entry['modified']:
                    print " - got new entries"
                    c.execute('update bookmark set stale = 0 where feed_id = ?', (entry['feed_id'],))
            else:
                print " - feed not modified"

        db.commit()

    except sqlite3.Error, e:
        print "An error occurred:", e.args[0]

if __name__ == "__main__":
    main()
