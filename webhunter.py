import cherrypy
from hunter import Hunter

class Frontend:

    hunter = Hunter('Vintage-2010-08-01.db', False)

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

cherrypy.root = Frontend()

if __name__ == '__main__':
    target = cherrypy.server.start()
