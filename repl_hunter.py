"""repl_hunter.py

A crude REPL around a hunter object for searching cards from the command
line.  Mostly useful for system that don't have a proper sqlite3 tool on
hand.  May well be improved down the road.
"""

import sqlite3
from hunter import Hunter
from pprint import pprint
from sys import argv


if __name__ == '__main__':
    if len(argv) != 2:
        print 'Usage: repl_hunter.py file.(txt|db)'
        exit(1)
    HOBJ = Hunter(argv[1])
    USER = ''
    while USER != 'exit':
        USER = raw_input('> ')
        if USER == 'exit':
            exit(0)
        try:
            RESULTS = HOBJ.dbase.execute(USER).fetchall()
        except sqlite3.OperationalError as error:
            print 'sqlite3.OperationalError', error
        else:
            pprint(RESULTS)
            print len(RESULTS), 'results'
