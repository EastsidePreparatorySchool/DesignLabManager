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


ADMIN_USERNAMES = ["guberti", "qbowers", "jbriggs", "dclarke", "jnolan", "rmack"]
TOOLS = ["vinyl_cutter", "sewing_machine", "hand_tools", "epilog_laser", "universal_laser", "cnc", "printrbot", "robo3d", "soldering", "coffee_maker"]
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def log(text):
    logging.info("-------->" + text.upper() + "<--------")



class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    vinyl_cutter = ndb.IntegerProperty()
    sewing_machine = ndb.IntegerProperty()
    hand_tools = ndb.IntegerProperty()
    epilog_laser = ndb.IntegerProperty()
    universal_laser = ndb.IntegerProperty()
    cnc = ndb.IntegerProperty()
    printrbot = ndb.IntegerProperty()
    robo3d = ndb.IntegerProperty()
    soldering = ndb.IntegerProperty()
    coffee_maker = ndb.IntegerProperty()

class BaseHandler(webapp2.RequestHandler):
    
    def name(self):
        auth = self.request.cookies.get('auth')
        if not (auth):
            return None
        return json.loads(auth)['username']

       
        

    def email_to_id(self, email):
        name = string.split(email, "@")[0].lower()
        for student in ID_TABLE:
            if (student[0] == name):
                return student[1]
        return None

    def db_user_to_simple_obj(self, obj):
        return {
            'sid': obj.sid,
            'fullname': obj.fullname,
            'vinyl_cert_level': obj.vinyl_cert_level,
            'sewing_machine_cert_level': obj.sewing_machine_cert_level,
            'hand_tools_cert_level': obj.hand_tools_cert_level,
            'epilog_cert_level': obj.epilog_cert_level,
            'universal_laser_cert_level': obj.universal_laser_cert_level,
            'cnc_cert_level': obj.cnc_cert_level,
            'printrbot_cert_level': obj.printrbot_cert_level,
            'robo3d_cert_level': obj.robo3d_cert_level,
            'makerbot_cert_level': obj.makerbot_cert_level,
            'soldering_cert_level': obj.soldering_cert_level,
            'power_tools_cert_level': obj.power_tools_cert_level,
            'coffee_maker_cert_level': obj.coffee_maker_cert_level
        };

class IndexHandler(BaseHandler):
    def get(self):
        loggedin = False
        name = self.name()
        if (name):
            loggedin = True
        
        template = JINJA_ENVIRONMENT.get_template('public/index.html')
        self.response.write(template.render({
            'loggedin': loggedin,
            'name': name
        }))
         
        #user_id = int(str_id)
#
#        query = User.query(User.sid == user_id)
#        for db_obj in query: # Will only ever be one
#            template_values = { \
#            'sid': db_obj.sid, \
#            'fullname': db_obj.fullname, \
#            'sewing_machine_cert_level': db_obj.sewing_machine_cert_level, \
#            'soldering_cert_level': db_obj.soldering_cert_level, \
#            }
#            template = JINJA_ENVIRONMENT.get_template('index.html')
##            self.response.write(template.render(template_values))
#           break

class LoginHandler(BaseHandler):
    
    def get(self):
        log('get request')
        template = JINJA_ENVIRONMENT.get_template('public/login.html')
        self.response.write(template.render({}))

    def post(self):
        username = string.split(request.get('email'), "@")[0].lower()
        password = self.request.get('password')

        if (authenticate_user.auth_user(username, password)):
            now = datetime.datetime.now()
            obj = {
                "username": username,
                "time_issued": now.isoformat()
            }
            self.response.set_cookie('auth', json.dumps(obj), expires= now+datetime.timedelta(2))
            self.response.write("")
            # Now, if user does not already have a database object, make them one

        else:
            self.response.write("Username or password was incorrect")

class ToolHandler(BaseHandler):
    def get(self, tool):
        if tool not in TOOLS:
            self.error(404)
            return

        resp = "This is the future home of the " + tool + " page."
        login = self.get_id()
        if login:
            resp += "\n\nYou are currently logged in as " + login
        else:
            resp += "\n\nYou are not currently logged in. <a href='/login'>LOGIN</a>"

        self.response.write(resp)

app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/login', LoginHandler),
    ('/tool/([\w\-]+)', ToolHandler)
], debug=True)
