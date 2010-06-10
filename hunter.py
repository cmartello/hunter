"""hunter.py --- An alternative to WOTC's "Gatherer" """


from string import replace
from re import search, match
from sqlite3 import connect


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
            self.db = connect(filename)

    def parse_oracle(self, filename):
        """Parses an 'oracle' text file and converts it to a database.

        The database filename is simply the original filename with ".txt"
        replaced with ".db".  Nothing prevents the user from changing this
        later.
        """

        # open up the original file
        oracle = open(filename, 'r')

        # create the database
        dbname = replace(filename, '.txt', '.db')
        self.db = connect(dbname)

        # this will be used later when determining if a given line
        # describes the type of the card
        types = set(['Artifact', 'Tribal', 'Legendary', 'Land', 'Snow', 
            'Creature', 'Sorcery', 'Instant', 'Planeswalker', 
            'Enchantment', 'World', 'Basic', ''])

        # create the 'cards' table
        self.db.execute('''CREATE TABLE cards
            (
                cardid INTEGER PRIMARY KEY,
                cardname TEXT,
                castcost TEXT,
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
            line = replace(line, "'", "''")

            # the first line of an entry is ALWAYS the name of the card
            if entline == 1:
                entry['cardname'] = line
                continue

            # match a casting cost
            rx = match('^(X{1,2}|)([WUBRG0-9]|\([wubrg2]\/[wubrg]\))+$', line)
            if rx is not None:
                entry['castcost'] = line
                continue

            # check to see if the line identifies the type of the card
            # only do this if we haven't already
            if entry.get('type', None) is None:
                rx = search('--', line)
                if rx is not None:
                    rx = match('(.+)--', line)
                    a = set(rx.group(1).split(' '))

                if rx is None:
                    a = set(line.split(' '))

                if a <= types:
                    entry['type'] = line
                    continue

            # match power/toughness
            rx = match('^([0-9*+]{1,3})\/([0-9*+]{1,3})$', line)
            if rx is not None:
                entry['power'] = rx.group(1)
                entry['toughness'] = rx.group(2)
                continue

            # match publication info
            rx = match('^[A-Z0-9]{1,5}-[LCURMS]', line)
            if rx is not None:
                entry['printings'] = line
                continue

            # an empty line indicates the end of an entry
            rx = match('^$', line)
            if rx is not None:
                self.db.execute("insert into cards values ('" +\
                    str(cardid) +\
                    "','" + entry['cardname'] +\
                    "','" + entry.get('castcost', 'N/A') +\
                    "','" + entry['type'] +\
                    "','" + entry.get('power', '-') +\
                    "','" + entry.get('toughness', '-') +\
                    "','" + entry.get('printings', '???') +\
                    "','" + entry.get('text', '') + "')")
                self.db.commit()

                #reset state, bump ID up
                entry = dict()
                cardid += 1
                entline = 0
                continue

            # if the line doesn't match anything else, it's card text.
            entry['text'] = entry.get('text', '') + line + '\n'

        

    def raw_query(self, querystring):
        """Sends a raw SQL query to the database and returns the results.
        Basically little more than a wrapper around the sqlite3 functions
        and SHOULD NEVER BE USED WITH UNTRUSTED DATA.  DO NOT USE THIS AS
        PART OF A CGI SCRIPT UNLESS YOU KNOW EXACTLY WHAT THE ---- YOU ARE
        DOING!!!
        """
        pass

if __name__ == "__main__":
    a = Hunter('oracle.txt')
