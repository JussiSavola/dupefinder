#!/usr/bin/env python2.7

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
from os.path import join, getsize, islink, isdir, basename
import hashlib
from sys import argv
import socket

SKIP_FILES = ['.DS_Store', '.PKG', '.media']
DEBUG = 1


def warn(msg):
    sys.stderr.write(msg + "\n")


def debug(msg):
    if DEBUG > 0:
        warn(msg)


class MemStore:
    def __init__(self, name):
        self.name = name
        self.store = []

    def add(self, filename, filesize, digest, ftime):
        self.store.append((self.name, filename, filesize, digest, ftime))

    def output_dupes(self):
        print("Printing all dupes: ")
        for (sysname, filename, size, digest, ftime) in self.store:
            print (digest, size, filename)

    def commit(self):
        pass

    def finish(self):
        pass


class DbStore:
    def __init__(self, name):
        self.name = name
        self.conn = sqlite3.connect(name)

        self.__ensure_table_present()

        self.cursor = self.conn.cursor()
        self.buf_count = 0
        self.batch_size = 100

    def add(self, filename, filesize, digest, ftime):
        sql = "INSERT INTO files VALUES (?,?,?,?,?,?,?,?)"
        self.cursor.execute(sql, (self.name, filename, filesize, digest, ftime,'0','0','0'))

        self.buf_count += 1
        if self.buf_count >= self.batch_size:
            self.commit()
            self.buf_count = 0

    def commit(self):
        self.conn.commit()

    def finish(self):
        self.conn.close()

    def output_dupes(self):
        self.cursor.execute("select md5sum, size, fullname from files where (md5sum) in "
                            "(select md5sum from files group by md5sum having count(*) > 1) order by md5sum")

        rows = self.cursor.fetchall()
        print
        print("Printing all dupes: ")
        for row in rows:
            print row
            self.cursor.execute("""UPDATE files SET duplicate = ? where md5sum = ? """, ('1', row[0]))
            self.conn.commit()

    def __ensure_table_present(self):
        self.conn.cursor().execute('''CREATE TABLE IF NOT EXISTS files
            (hostname text, fullname text, size text, md5sum text, filetime text, nukeme text, \
            mastercopy text, duplicate text)''')
        self.conn.commit()


class DupChecker:
    def __init__(self, store, minsize=40000, blocksize=16000, skip_files=[]):
        self.store = store
        self.minsize = minsize
        self.blocksize = blocksize
        self.skip_files = SKIP_FILES + skip_files

    @staticmethod
    def is_regular(fpath):
        return os.path.isfile(fpath) and not os.path.islink(fpath)

    @staticmethod
    def trim_str(str, maxlen):
        if len(str) > maxlen:
            chunk = maxlen/2 - 2
            return str[0:chunk] + '...' + str[-chunk:]
        else:
            return str

    def store_checksum(self, fullname, filesize):
        current_file = open(fullname, 'rb')
        try:
            file_beginning = current_file.read(self.blocksize)
            current_file.seek(-self.blocksize, 2)  # last bytes of the file
            file_end = current_file.read(self.blocksize)
            file_chunk = file_beginning + file_end
            digest = hashlib.md5(file_chunk).hexdigest()
        except StandardError, err:
            warn("Unable to read file ", fullname, err)
            return
        finally:
            current_file.close()

        self.store.add(unicode(fullname, 'latin-1'), filesize, digest, '3')
        return digest

    def skippable(self, filename):
        basename(filename) in self.skip_files

    def run(self, args):
        print("fs encoding is ", sys.getfilesystemencoding())
        print

        if len(args) > 0:
            start_point = args[0]
        else:
            start_point = '.'

        debug("using {} as starting point".format(start_point))
        print
        fmt = "{:<60} {:>10} {:>10}"

        debug(fmt.format("Full path", "Size", "Digest"))

        for root, dirs, files in os.walk(start_point):
            for nativename in files:

                fullname = join(root, nativename)
                if isdir(fullname) or islink(fullname) or self.skippable(fullname):
                    continue

                try:
                    filesize = getsize(fullname)

                    if not self.is_regular(fullname):
                        debug("{}: is not a regular file, skipping".format(fullname))
                    elif filesize < self.minsize:
                        tmpl = "{}: file size too small ({}), not entering db"
                        debug(tmpl.format(fullname, filesize))
                    else:
                        digest = self.store_checksum(fullname, filesize)

                        debug(fmt.format(self.trim_str(fullname, 60), filesize, digest))

                except IOError as e:
                    print("kuukkeliskuu: " + e)

        self.store.commit()
        self.store.output_dupes()
        self.store.finish()


if __name__ == "__main__":
    systemname = socket.gethostname()

    print("my system name", systemname)
    store_name = systemname + ".db"
    print("db file name: ", store_name)

    store = DbStore(store_name)
    #  store = MemStore(store_name)

    dc = DupChecker(store)
    dc.run(argv[1:])
