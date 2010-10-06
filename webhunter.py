import cherrypy
from sys import argv
from hunter import Hunter

class Frontend:

    def __init__(self, dbfilename):
        self.hunter = Hunter(dbfilename, False)

    def index(self, query=None):
        if query is not None:
            q = self.hunter.raw_query(query)
            output = ''
            for a in q:
                for b in a:
                    output += ' ' + str(b)
                output += '<br />\n'
            return output
        else:
            a = open('index.html', 'r')
            return a.readlines()

    index.exposed = True


if __name__ == '__main__':
    if len(argv) != 2:
        print 'Usage: webhunter.py file.db'
        exit(1)

    cherrypy.root = Frontend(argv[1])
    target = cherrypy.server.start()
