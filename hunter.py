"""hunter.py --- An alternative to WOTC's "Gatherer" """


import sqlite3
from re import search, match
from sqlite3 import connect
from sys import argv, exit
from pprint import pprint


class Hunter:
    """The actual hunter object for making queries of the card databse, set
    up with an oracle .txt file or a database file that is simply loaded
    and queried with SQLite.  Provides a simple front end around the actual
    queries for the user.
    """

    def __init__(self, filename):
        """Accepts a filename and sets up services as dictated by the
        filename; if the filename ends in ".db" it simply opens a database
        connection to the file.  If the filename ends in ".txt", it parses
        the text file and creates an appropriate database file, then loads
        that instead.
        """

        # check to see what kind of file has been specified
        res = search('(\.txt|\.db)$', filename)
        if res.group(1) == '.txt':
            self.parse_oracle(filename)
        if res.group(1) == '.db':
            self.dbase = connect(filename)

    def parse_oracle(self, filename):
        """Parses an 'oracle' text file and converts it to a database.

        The database filename is simply the original filename with ".txt"
        replaced with ".db".  Nothing prevents the user from changing this
        later.
        """

        # open up the original file
        oracle = open(filename, 'r')

        # create the database
        dbname = filename.replace('.txt', '.db')
        self.dbase = connect(dbname)

        # this will be used later when determining if a given line
        # describes the type of the card
        types = set(['Artifact', 'Tribal', 'Legendary', 'Land', 'Snow',
            'Creature', 'Sorcery', 'Instant', 'Planeswalker',
            'Enchantment', 'World', 'Basic', ''])

        # create the 'cards' table
        self.dbase.execute('''CREATE TABLE cards
            (
                cardid INTEGER PRIMARY KEY,
                cardname TEXT,
                castcost TEXT,
                loyalty TEXT,
                type TEXT,
                power TEXT,
                toughness TEXT,
                printings TEXT,
                cardtext TEXT
            ) ''')

        # state variables
        cardid = 0
        entline = 0
        entry = dict()

        # parsing loop
        for line in oracle.readlines():
            entline += 1
            line = line[:-1]

            # escape single quotes
            line = line.replace("'", "''")

            # the first line of an entry is ALWAYS the name of the card
            if entline == 1:
                entry['cardname'] = line
                continue

            # match a casting cost
            regex = match(\
                '^(X{1,2}|)([WUBRG0-9]|\([wubrg2]\/[wubrg]\))+$', line)
            if regex is not None:
                # Don't overwrite casting cost if its already there
                if entry.get('castcost') == None:
                    entry['castcost'] = line
                    continue
                # if we're dealing with a planeswalker and the line is just a 1 or 2 digit number,
                # file that under loyalty.
                elif entry.get('type')[:12] == 'Planeswalker' and match('^(\d{1,2})$', line) is not None:
                    entry['loyalty'] = line
                    continue

            # check to see if the line identifies the type of the card
            # only do this if we haven't already
            if entry.get('type', None) is None:
                regex = search('--', line)
                if regex is not None:
                    regex = match('(.+)--', line)
                    words = set(regex.group(1).split(' '))

                if regex is None:
                    words = set(line.split(' '))

                if words <= types:
                    entry['type'] = line
                    continue

            # match power/toughness
            regex = match('^([0-9*+]{1,3})\/([0-9*+]{1,3})$', line)
            if regex is not None:
                entry['power'] = regex.group(1)
                entry['toughness'] = regex.group(2)
                continue

            # match publication info
            regex = match('^[A-Z0-9]{1,5}-[LCURMS]', line)
            if regex is not None:
                entry['printings'] = line
                continue

            # an empty line indicates the end of an entry
            regex = match('^$', line)
            if regex is not None:
                self.dbase.execute("insert into cards values ('" +\
                    str(cardid) +\
                    "','" + entry['cardname'] +\
                    "','" + entry.get('castcost', 'N/A') +\
                    "','" + entry.get('loyalty', 'N/A') +\
                    "','" + entry['type'] +\
                    "','" + entry.get('power', '-') +\
                    "','" + entry.get('toughness', '-') +\
                    "','" + entry.get('printings', '???') +\
                    "','" + entry.get('text', '') + "')")

                #reset state, bump ID up
                entry = dict()
                cardid += 1
                entline = 0
                continue

            # if the line doesn't match anything else, it's card text.
            entry['text'] = entry.get('text', '') + line + '\n'

        # commit the table to the db
        self.dbase.commit()


def repl():
    # REPL for SQL statements
    user = ''
    while user != 'exit':
        user = raw_input('> ')
        try:
            results = test.dbase.execute(user).fetchall()
        except sqlite3.OperationalError as e:
            print 'sqlite3.OperationalError', e
        else:
            pprint(results)
            print len(results), 'results'


if __name__ == "__main__":
    if len(argv) != 2:
        print "Usage: hunter.py file.txt\n"
        exit(1)

    test = Hunter(argv[1])


