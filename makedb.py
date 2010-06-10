from re import match, search
from sqlite3 import connect
from string import replace

# open things up
oracle = open('oracle.txt', 'r')
db = connect('oracle.db')

# card type set
types = set(['Artifact', 'Tribal', 'Legendary', 'Land', 'Snow', 'Creature',
    'Sorcery', 'Instant', 'Planeswalker', 'Enchantment', 'World', 'Basic',
    ''])

# create the 'cards' table
db.execute('''CREATE TABLE cards
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

# a couple state variables
cardid = 0
entline = 0
entry = dict()

# start parsing the monster
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
        db.execute("insert into cards values ('" + str(cardid) +\
            "','" + entry['cardname'] +\
            "','" + entry.get('castcost', 'N/A') +\
            "','" + entry['type'] +\
            "','" + entry.get('power', '-') +\
            "','" + entry.get('toughness', '-') +\
            "','" + entry.get('printings', '???') +\
            "','" + entry.get('text', '') + "')")
        db.commit()

        # reset state, bump ID up
        entry = dict()
        cardid += 1
        entline = 0
        continue

    # if it doesn't match anything else, assume that it is card text
    entry['text'] = entry.get('text', '') + line + '\n'
