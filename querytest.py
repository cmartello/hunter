import cherrypy
from hunter import Hunter

cherrypy.root = Hunter('Vintage-2010-08-01.db', False)

if __name__ == '__main__':
    target = cherrypy.server.start()
