#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# dupe killer - Jussi Savola  2017
#
# Usage: python dupekiller.py 
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



def kill_marked_files(c):
    c.execute("select fullname from files where nukeme is '1'")

    rows = c.fetchall()
    # print rows
    for row in rows:
        print row
        try:
            os.remove(row[0])
            # c.execute("delete from files where ...
        except:
            print ("Can't find file " + row[0])






def main(argv):
    if len(argv) > 1:
        dbfile = argv[1]
    else:
        print ("give db filename as argument")
        sys.exit(-1)

    print ("db file name: ", dbfile)


    if not exists(dbfile):
        print ("give db filename as argument")
        sys.exit(-2)

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    kill_marked_files(c)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main(argv)
