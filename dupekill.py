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



def output_dupes(c):
    c.execute("select md5sum, size, fullname  from files where (md5sum) in "
              "(select md5sum from files group by md5sum having count(*) > 1) order by md5sum")

    rows = c.fetchall()
    print rows
    for row in rows:
        print row

def get_list_of_nonmaster_copies(c):
    a = c.execute("select fullname from files where md5sum in (select md5sum from files "
                  " group by md5sum, mastercopy having mastercopy = '1') and mastercopy != '1'")
    rows = c.fetchall()
    return rows

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
    list = get_list_of_nonmaster_copies(c)
    conn.close()

    for entry in list:
        try:
            a  = str(entry[0])
            print ("about to remove " + a)
            os.remove(a)
            print ("... removed " + a)
            # print ('would be erasing: ' + '"'+str(entry)+'"')
        except:
            print ("skipping: " + str(entry))


if __name__ == "__main__":
    main(argv)
