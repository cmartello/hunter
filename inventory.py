import cherrypy
from re import search, match
from sqlite3 import connect
from os.path import isfile
from hunter import Hunter
from sys import argv

class Inventory:
    def __init__(self, oraclefile, inventoryfile):
        # open main hunter object; it's the basis of the the entire
        # inventory system
        self.cardbase = Hunter(oraclefile, False)
        
        # if the inventory files doesn't exist, create it.
        if not isfile(inventoryfile):
            self.inv_db = connect(inventoryfile)
            
            # create the main table
            self.inv_db.execute('''CREATE TABLE inventory
                (
                    entry INTEGER PRIMARY KEY AUTOINCREMENT,
                    cardname TEXT,
                    version TEXT,
                    quantity INTEGER
                )''')

            # get the file format info from the cardbase
            schema, fbase = \
                cardbase.execute("select * from format").fetchall()[0]

            # create the format table and write the file format info to it
            self.inv_db.execute('''CREATE TABLE format
                (
                    schema INTEGER,
                    basefile TEXT
                ) ''')

            self.inv_db.execute('''INSERT INTO format VALUES ('''+\
                str(schema) + ', "' fbase + '")'



if __name__ == '__main__':
    if len(argv) != 3:
        print 'Usage: inventory.py oracle.db yourinventory.db'
        exit(1)

    # if the inventory file doesn't exist, it'll have to be created
