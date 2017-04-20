#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# dupe finder - Jussi Savola 2013, 2017
# This program creates a sqlite3 db and enters information on files into the database
# after this, user can use the db to find out duplicate files :)
#
# Usage: python dupe.py [optional directory]
#
# Disclaimer: If this breaks your files or your system, you can keep all the parts

import sqlite3
import os
import sys
import fnmatch
from os.path import join, getsize, exists
import hashlib
from stat import *
from sys import argv
import socket


def create_db_table(c):
    c.execute('''CREATE TABLE files
        (hostname text, fullname text, size text, md5sum text, filetime text, nukeme text, mastercopy text, duplicate text)''')


def output_dupes(c):
    c.execute("select md5sum, size, fullname  from files where (md5sum) in "
              "(select md5sum from files group by md5sum having count(*) > 1) order by md5sum")

    rows = c.fetchall()
    # print rows
    for row in rows:
        print row
        c.execute("UPDATE files SET duplicate = ? where md5sum = ?", ('1', row[0]))


def is_regular(fullname):
    try:
        mode = os.stat(fullname).st_mode
        if S_ISREG(mode) and not os.path.islink(fullname):  # Only regular files considered
            return True
        else:
            return False
    except:
        return False

def skip_this(fullname):
    if ".DS_Store" in fullname or '.PKG' in fullname or  '.media' in fullname:
        return True
    else:
        return False

def main(argv):
    mysystemname = socket.gethostname()
    print ("my system name", mysystemname)
    dbfile = mysystemname + ".db"
    print ("db file name: ", dbfile)
    print ("in main")
    print ("fs encoding is ", sys.getfilesystemencoding())
    print

    minsize = 40000
    i = 0
    file_start_size = 32000
    file_end_size = 32000

    if not exists(dbfile):
        conn = sqlite3.connect(dbfile)
        print ("conn", conn)
        c = conn.cursor()
        print ("c", c)
        print ("db file does not exist. creating")
        create_db_table(c)
        conn.commit()
        conn.close()

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    if len(argv) > 1:
        start_point = argv[1]
    else:
        start_point = '.'

    for root, dirs, files in os.walk(start_point):
        for nativename in files:
            i += 1
            if i > 100:
                i = 0
                conn.commit()

            # print ("name: ", nativename)
            try:
                fullname = join(root, nativename)
                if not skip_this(fullname):
                    try:
                        statinfo = os.stat(fullname)
                        filesize = statinfo.st_size
                    except:
                        filesize = 0
                    # print ("File exists.", fullname)
                    if filesize > minsize and is_regular(fullname):
                        current_file = open(fullname, 'rb')
                        try:
                            file_beginning = current_file.read(file_start_size)
                            current_file.seek(-file_end_size, 2)  # last bytes of the file
                            file_end = current_file.read(file_end_size)
                            file_chunk = file_beginning + file_end
                            myhash = hashlib.md5(file_chunk).hexdigest()
                        # print ("myhash is ", myhash)
                        except:
                            print ("Unable to read the file")
                            break
                        current_file.close()

                        print "full filename, size:", fullname, filesize
                        utf8name = unicode(fullname, 'latin-1')

                        c.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?,?)",
                            (mysystemname, utf8name, filesize, myhash, '3','0','0','0'))
                    else:
                        try:
                            print (str(fullname) + " file size too small (" + str(filesize) + "), or some other"
                                   " other oddity. maybe a link.")
                        except:
                            print ("Something too funny with filename, skipping")
                            print
                else:
                    print ("skipping: ", fullname)

            except IOError as e:
                print ("kuukkeliskuu")

    output_dupes(c)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main(argv)
