import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2
import logging
import json
import string
import datetime
import authenticate_user


ADMIN_USERNAMES = ['guberti', 'qbowers', 'jbriggs', 'dclarke', 'jnolan', 'rmack']
TOOLS = ['vinyl_cutter', 'sewing_machine', 'hand_tools', 'epilog_laser', 'universal_laser', 'cnc', 'printrbot', 'robo3d', 'soldering', 'coffee_maker']
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)



class User(ndb.Model):
    uid = ndb.IntegerProperty(required=True)
    vinyl = ndb.IntegerProperty(default=0)
    sewing = ndb.IntegerProperty(default=0)
    tools = ndb.IntegerProperty(default=0)
    epilog = ndb.IntegerProperty(default=0)
    universal = ndb.IntegerProperty(default=0)
    cnc = ndb.IntegerProperty(default=0)
    printrbot = ndb.IntegerProperty(default=0)
    robo3d = ndb.IntegerProperty(default=0)
    soldering = ndb.IntegerProperty(default=0)
    coffee = ndb.IntegerProperty(default=0)

def log(text):
    logging.info('-------->' + text.upper() + '<--------')
def newUser(name):
    user = User(uid = name_to_id(name))
    user.key = ndb.Key(User, name_to_id(name))
    user.put()


def name_to_id(name):
    for student in ID_TABLE:
        if (student[0] == name):
            return student[1]
    return None
    
def email_to_name(email):
    return string.split(email, '@')[0].lower()


class BaseHandler(webapp2.RequestHandler):
    
    def name(self):
        auth = self.request.cookies.get('auth')
        if not (auth):
            return None
        return json.loads(auth)['username']
	
    def getobj(self, name):
        user = ndb.Key(User, name).get()
        if user:
            return user
        return None
    
    
class IndexHandler(BaseHandler):
    def get(self):
        loggedin = False
        admin = False
        user = False
        
        name = self.name()
        if (name):
            loggedin = True
            if(name == 'admin'):
                admin = True
            else:
                user = True
        
        
        
        template = JINJA_ENVIRONMENT.get_template('public/index.html')
        self.response.write(template.render({
            
            
            'loggedin': loggedin,
            'name': name,
            'tool': {'name': 'printrbots', 'level': 2},
            'tools': [
                {'name': 'printrbots', 'level': 2},
                {'name': 'robos', 'level': 2},
                {'name': 'THAT ONE DEMON OF MADNESS', 'level': 2}
            ]
        }))

class ToolHandler(BaseHandler):
    def get(self, tool):
        loggedin = False
        admin = False
        user = False
        
        name = self.name()
        if (name):
            loggedin = True
            if(name == 'admin'):
                admin = True
            else:
                user = True
        
        template = JINJA_ENVIRONMENT.get_template('public/tool.html')
        self.response.write(template.render({
            
            
            'loggedin': loggedin,
            'name': name,
            'tool': {
				'name': 'printrbot',
				'level': 2,
				'macros': '/public/macros/printrbot.html'
			},
			'level': 5,
        }))


class LoginHandler(BaseHandler):
    def post(self):
        username = string.split(self.request.get('email'), '@')[0].lower()
        password = self.request.get('password')

        if (authenticate_user.auth_user(username, password)):
            now = datetime.datetime.now()
            obj = {
                'username': username,
                'time_issued': now.isoformat()
            }
            self.response.set_cookie('auth', json.dumps(obj), expires= now+datetime.timedelta(2))
            self.response.write('')
			
            # Now, if user does not already have a database object, make them one
            if not self.getobj:
                user = User(username = username)
                user.key = ndb.Key(User, username)
                user.put()

        else:
            self.response.write('Username or password was incorrect')



app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/tool/([\w\-]+)', ToolHandler),
    ('/login', LoginHandler),
    ('/admin', )
], debug=True)
