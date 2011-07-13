"""hunter.py --- An alternative to WOTC's "Gatherer" """


import re
from re import search, match
from sqlite3 import connect
from sys import argv


def card_color(mana, cardname, text):
    '''Determines a card's color by its casting cost and by checking card
    text (for special cases like colored zero-cost spells and so forth.)
    Returns a text string that matches the card's color(s).'''
    color_letters = 'WUBRG'
    color_names = {'black': 'B', 'blue': 'U', 'green': 'G', 'red': 'R', \
        'white': 'W', 'colorless': '', 'all colors': 'WUBRG'}
    colors = ''
    clean_mana = [x.upper() for x in mana if x not in '0123456789()x/']
    for letter in color_letters:
        if clean_mana.count(letter) > 0:
            colors += letter

    searchstring = cardname +\
        ' is (white|blue|black|red|green|colorless|all colors)'
    regex = search(searchstring, text)
    if regex is not None:
        if regex.group(1) in color_names.keys():
            colors = color_names[regex.group(1)]
    return colors


def mana_cost(text):
    '''Accepts a text string that matches the (awful) regular expression
    of a mana cost and returns an integer for the converted mana cost of
    a spell.
    '''
    # strip Xs from cost
    text = text.replace('X', '')

    # look for and count up the 'split' mana symbols
    hybrid = 0
    nohy = ''
    cost = text.replace('(', ')').split(')')
    for token in cost:
        regex = match('[wubrg]/[wubrgp]', token)
        if regex != None:
            hybrid += 1
            continue
        regex = match('(\d)/[wubrg]', token)
        if regex != None:
            hybrid += int(regex.group(1))
            continue
        nohy += token

    text = nohy

    # handle split cards via recursion.
    regex = match('([WUBRG0-9\(\)]+) // ([WUBRG0-9\(\)]+)', text, re.I)
    if regex != None:
        return mana_cost(regex.group(1)) + mana_cost(regex.group(2))

    # most basic mana costs can be handled this way
    regex = match('(\d+|)(([WUBRG])+|)', text)

    # the preceding '0' is to prevent int() from crying about getting a
    # zero-length string.
    return int('0' + regex.group(1)) + len(regex.group(2)) + hybrid


def determine_cgroup(user):
    """Determines roughly what group a given card should be in for the
    purpose of figuring collector numbers returns an integer to tell
    what group.
    """

    # dict for color->group mapping
    colors = {'W': 20, 'U': 30, 'B': 40, 'R': 50, 'G': 60, \
        'WU': 0, 'UB': 1, 'BR': 2, 'RG': 3, 'WG': 4,\
        'WB': 5, 'UR': 6, 'BG': 7, 'WR': 8, 'UG': 9,\
        'WUB': 10, 'UBR': 11, 'BRG': 12, 'WRG': 13, 'WUG': 14,\
        'WUBRG': 15}


    # basic colors (W=20, U=30, B=40, R=50, G=60)
    if len(user.get('color')) == 1:
        return colors[user.get('color')]

    # colorless cards -- artifacts go to 130, non-artifacts and lands get 10
    if user.get('color') == '':
        if re.search('Artifact', user.get('type')) is not None:
            return 130
        if re.search('(Artifact|Land)', user.get('type')) is None:
            return 10

    # basic lands
    if re.search('Basic', user.get('type')) is not None:
        return 150

    # other lands
    if re.search('Land', user.get('type')) is not None:
        return 140

    # split cards
    if re.search('\/\/', user.get('cardname')) is not None:
        return 120

    # cards with hybrid mana
    if re.search('\(([wubrg]|\d)\\/[wubrg]\)', user.get('castcost', '')) is not None:

        # special cases for Shadowmoor, Eventide, and Alara Reborn
        if re.search('(SHM|EVE|ARB)-', user.get('printings')) is not None:
            # Monocolored hybrid just counts as the usual color.
            if len(user.get('color', None)) == 1:
                return colors[user.get('color')]

            # Multicolored stuff goes in a particular order for these sets
            if len(user.get('color')) == 2 or len(user.get('color')) == 3:
                return colors[user.get('color')] + 100

        # Default is group 100
        return 100

    # default (unimplemented stuff, usually basic multicolor.)
    # special case for Alara Reborn
    if re.search('ARB', user.get('printings')) is not None:
        return 70 + colors[user.get('color')]
    return 70


def filtered_file(filename, seperator=':'):
    """Returns an interator that automatically does three things with a
    specified file:
    * Turns apostrophes into SQLite's escaped apostrophes.
    * Ignores blank lines and comments.
    * Splits a line by the specified seperator icon. -- In this program, it's
      always a colon.
    """
    for line in open(filename, 'r'):
        # ignore blank lines
        regex = match('^$', line)
        if regex is not None:
            continue

        # ignore comments at the beginning of a line
        regex = match('^#', line)
        if regex is not None:
            continue

        # escape single quotes
        line = line.replace("'", "''")

        # split the line by the seperator and yield it
        yield line.split(seperator)


def build_tables(connection, filename):
    """Creates the tables that will be used in a typical Hunter databse."""

    # create a table to identify the .db for later
    connection.execute('''CREATE TABLE format
        (
            schema INTEGER,
            basefile TEXT
        ) ''')

    connection.execute('''INSERT INTO format VALUES (25, "''' + filename + '")')

    # create the 'cards' table
    connection.execute('''CREATE TABLE cards
        (
            cardid INTEGER PRIMARY KEY AUTOINCREMENT,
            cardname TEXT,
            castcost TEXT,
            color TEXT,
            con_mana INTEGER,
            loyalty TEXT,
            type TEXT,
            power TEXT,
            toughness TEXT,
            v_hand TEXT,
            v_life TEXT,
            cn_position INTEGER,
            cardtext TEXT
        ) ''')

    # create a table for publication data
    connection.execute('''CREATE TABLE published
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            expansion TEXT,
            rarity TEXT
        ) ''')

    # create a table for the setlist
    connection.execute('''CREATE TABLE sets
        (
            abbreviation TEXT,
            setname TEXT,
            released TEXT
        ) ''')

    # read a list of sets from setlist.txt
    for data in filtered_file('setlist.txt'):
        connection.execute("INSERT INTO sets VALUES (" +\
            "'" + data[1] +\
            "','" + data[0] +\
            "','" + data[2] +\
            "')")

    # create a table for legal sets for given formats
    connection.execute('''CREATE TABLE legalsets
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            format TEXT,
            expansion TEXT
        )''')

    # read in formats.txt, using it to fill the legalsets table
    formats = open('formats.txt', 'r')

    for data in filtered_file('formats.txt'):
        for expansion in data[1].split(','):
            connection.execute("INSERT INTO legalsets (format,expansion) " +\
                "VALUES ('" + data[0] + "','" + expansion + "')")

    # close the formats file
    formats.close()

    # create a table for banned/restricted cards
    connection.execute('''CREATE TABLE badcards
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            format TEXT,
            card TEXT,
            status TEXT
        ) ''')

    # read in a list of banned/restricted cards
    for data in filtered_file('bans.txt'):
        connection.execute('''INSERT INTO badcards (format,status,card) ''' +\
            '''VALUES ('%s','%s','%s')''' % (data[0], data[1], data[2]))

    # commit the DB and we're done.
    connection.commit()


def printings_data(connection, cardname, printings):
    """Takes the cardname and list of printings, converts them to a series of
    insertions for the 'published' table."""

    for expansion in printings.split(', '):
        regex = match('(.+)-([LCURMS])', expansion)
        connection.execute("INSERT INTO published " +\
        "(name, expansion, rarity) VALUES ('%s','%s','%s')"\
        % (cardname, regex.group(1), regex.group(2)))


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

        Performs other setup functions along the way, mostly just initilizing
        a few tables that are used by other functions.
        """

        # this will be used later when determining if a given line
        # describes the type of the card
        self.types = set(['Artifact', 'Tribal', 'Legendary', 'Land', 'Snow',
            'Creature', 'Sorcery', 'Instant', 'Planeswalker', 'Enchantment',
            'World', 'Basic', '//', 'Vanguard', 'Scheme', 'Plane',
            'Ongoing', ''])

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

        # build the tables
        build_tables(self.dbase, filename)

        # state variables
        entry, entline = dict(), 0

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
                '''^(
                        X{1,2}| #match 1 or 2 'x's at the beginning
                    )
                    (
                        [WUBRG0-9]|\([wubrg2]\/[wubrgp]\) # all digits, mana
                    )+
                    (|\s//\s    # break for split cards, repeat above
                        (
                            X{1,2}|
                        )
                        (
                            [WUBRG0-9]|\([wubrg2]\/[wubrg]\)
                        )+
                    )$''', line, re.X)
            if regex is not None:
                # Don't overwrite casting cost if its already there
                if entry.get('castcost') == None:
                    entry['castcost'] = line
                    entry['con_mana'] = mana_cost(line)
                    continue
                # if we're dealing with a planeswalker and the line is just
                # a 1 or 2 digit number, file that under loyalty.
                elif entry.get('type')[:12] == 'Planeswalker' and \
                match('^(\d{1,2})$', line) is not None:
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

                if words <= self.types:
                    entry['type'] = line
                    continue

            # match power/toughness -- if the card is a planeswalker, instead
            # put these data in as life/cards
            regex = match('^([0-9*+-]{1,3})\/([0-9*+-]{1,3})$', line)
            cardtype = search('(Creature|Vanguard)', entry.get('type', ''))
            if regex is not None and cardtype is not None:
                if cardtype.group(1) == 'Creature':
                    entry['power'] = regex.group(1)
                    entry['toughness'] = regex.group(2)
                if cardtype.group(1) == 'Vanguard':
                    entry['v_hand'] = regex.group(1)
                    entry['v_life'] = regex.group(2)
                continue

            # match publication info
            regex = match('^[A-Z0-9]{1,5}-[LCURMS]', line)
            if regex is not None:
                entry['printings'] = line
                continue

            # an empty line indicates the end of an entry
            regex = match('^$', line)
            if regex is not None:
                entry['color'] = card_color(entry.get('castcost', '-'), entry['cardname'], entry.get('text', ''))
                # determine roughly where the card should be sorted to
                entry['cn_position'] = determine_cgroup(entry)
                self.dbase.execute("INSERT INTO cards (" +\
                    "cardname, castcost, color, con_mana, loyalty, type, power, toughness, v_hand, v_life, cn_position, cardtext" +\
                    ")values ('" +\
                    entry['cardname'] +\
                    "','" + entry.get('castcost', '-') +\
                    "','" + entry.get('color') +\
                    "','" + str(entry.get('con_mana', 0)) +\
                    "','" + entry.get('loyalty', '-') +\
                    "','" + entry['type'] +\
                    "','" + entry.get('power', '-') +\
                    "','" + entry.get('toughness', '-') +\
                    "','" + entry.get('v_hand', '-') +\
                    "','" + entry.get('v_life', '-') +\
                    "','" + str(entry.get('cn_position', 0)) +\
                    "','" + entry.get('text', '') + "')")

                printings_data(self.dbase, \
                    entry['cardname'], entry.get('printings', '???'))

                #reset state, bump ID up
                entry, entline = dict(), 0
                continue

            # if the line doesn't match anything else, it's card text.
            entry['text'] = entry.get('text', '') + line + '\n'

        # commit the table to the db
        self.dbase.commit()


if __name__ == "__main__":
    if len(argv) != 2:
        print "Usage: hunter.py file.txt\n"
        exit(1)

    TEST = Hunter(argv[1])