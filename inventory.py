import cherrypy
import re
from re import search, match
from sqlite3 import connect
from os.path import isfile
from hunter import Hunter
from sys import argv


HTML_HEAD = '''
<HTML>
    <HEAD>
        <TITLE>Hunter-Inventory v0.1</TITLE>
    </HEAD>
    <BODY>
        <FORM action="search" method="get">
            <TABLE width=800>
                <TR>
                    <TD width=150><label for="query">select * from cards where:</LABEL>
                    <TD><input type="text" name="query" size=100 />
                </TR>
            </TABLE>
        </FORM>'''


HTML_FOOT = '''
    </BODY>
</HTML>'''

TABLE_HEAD = '''
    <FORM action="update_inventory" method="get">
        <TABLE width=850 border=1>
                <TR>
                    <TH>#
                    <TH>Cardname
                    <TH>Cost
                    <TH>Color
                    <TH>CMC
                    <TH>Type
                    <TH>P/T/L
                </TR>'''

TABLE_ROW = '''
                <TR>
                    <TD width=25><input name=%d type=text size=1 value=%d />
                    <TD width=150>%s
                    <TD width=75 align=center>%s
                    <TD width=100 align=center>%s
                    <TD width=25 align=center>%d
                    <TD width=200 align=center>%s
                    <TD width=* align=center>%s
                </TR>'''
# cardid, total in inventory, cardname, castcost, color, converted mana cost
# type, power/toughness or loyalty


TABLE_FOOT = '''
            </TABLE>
            <input type="submit" />
        </FORM>'''


def create_inventory_db(filename):
    inv_db = connect(filename)
            
    # create the main table
    inv_db.execute('''CREATE TABLE inventory
        (
            entry INTEGER PRIMARY KEY AUTOINCREMENT,
            cardid INTEGER,
            cardname TEXT,
            version TEXT,
            quantity INTEGER
        )''')

    inv_db.commit()

    return inv_db
    

class Inventory:
    def __init__(self, oraclefile, inventoryfile):
        # open main hunter object; it's the basis of the the entire
        # inventory system
        self.cardbase = Hunter(oraclefile, False)
        self.inventoryfile = inventoryfile

        # if the inventory files doesn't exist, create it.
        if not isfile(inventoryfile):
            self.inv_db = create_inventory_db(inventoryfile)
        else:
            self.inv_db = connect(inventoryfile)

        self.inv_db.close()

    def index(self):
        '''Does no more than show a simple query page.'''
        return HTML_HEAD + HTML_FOOT


    def search(self, query=None):
        '''Parses a SQL query and formats it nicely for the end user. This
        function mandates "select * from cards where " before the query as
        the columns are needed in a given order.
        '''

        if query is None:
            return HTML_HEAD + "<P>Empty query!</P>" + HTML_FOOT

        # first, query the hunter object
        rows = self.cardbase.raw_query('SELECT * FROM CARDS WHERE ' + query)

        # If there's no results, say so and abort.
        if len(rows) == 0:
            return HTML_HEAD + '<P>No results!</P>' + HTML_FOOT

        # begin generating output
        output = HTML_HEAD + TABLE_HEAD

        # tell the user how many results there were.
        output += '''<P>%d results returned.</P>''' % len(rows)

        for row in rows:
            # pull the quantity data from inventory
            self.inv_db = connect(self.inventoryfile)

            qcheck = self.inv_db.execute(\
                "SELECT quantity FROM inventory WHERE cardid = " + str(row[0]))
            quantity = sum(x[0] for x in qcheck)
            
            # default value for "power/toughness or loyalty
            ptl = 'N/A'

            # if the card is a creature, store its power/toughness for output
            if search('creature', row[6], re.I) is not None:
                ptl = row[7] + '/' +row[8]

            # if the card is a planeswalker, store its loyalty for output
            if search('planeswalker', row[6], re.I) is not None:
                ptl = row[5]

            # add the formatted row to the output
            output += (TABLE_ROW % (row[0], quantity, row[1], row[2], row[3], row[4], row[6], ptl))
        
        # add the footers
        output += (TABLE_FOOT + HTML_FOOT)
        
        # close the DB
        self.inv_db.close()

        return output


    def update_inventory(self, **args):
        output = ''
        for x in args.keys():
            output += str(x) + ',' + str(args[x]) + ',' + '\n<BR/>'
        return output

    index.exposed = True
    search.exposed = True
    update_inventory.exposed = True

if __name__ == '__main__':
    if len(argv) != 3:
        print 'Usage: inventory.py oracle.db yourinventory.db'
        exit(1)

    cherrypy.root = Inventory(argv[1], argv[2])
    target = cherrypy.server.start()
