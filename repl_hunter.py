import sqlite3
from hunter import Hunter
from sys import argv


if __name__ == '__main__':
    if len(argv) != 2:
        print 'Usage: repl_hunter.py file.(txt|db)'
        exit(1)
    hobj = Hunter(argv[1])
    user = ''
    while user != 'exit':
        user = raw_input('> ')
        try:
            results = hobj.dbase.execute(user).fetchall()
        except sqlite3.OperationalError as error:
            print 'sqlite3.OperationalError', error
        else:
            pprint(results)
            print len(results), 'results'
