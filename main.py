import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from slowaes import aes

import webapp2
import jinja2
import logging
import json
import string
import datetime
import authenticate_user
import base64



ADMIN_USERNAMES = ["guberti", "qbowers", "jbriggs", "dclarke", "jnolan", "rmack"]
TOOLS = ["vinyl_cutter", "sewing_machine", "hand_tools", "epilog_laser", "universal_laser", "cnc", "printrbot", "robo3d", "soldering", "coffee_maker"]
CRYPTO_KEY = open('data/crypto.key', 'rb').read()

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

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
    def get_id(self):
        if not (self.request.cookies.get("auth")):
            return None
        cookie = self.request.cookies.get("auth")
        
        decoded = aes.decryptData(CRYPTO_KEY, base64.b64decode(cookie))

        return json.loads(decoded)["username"]

    def send_login_response(self):
        template = JINJA_ENVIRONMENT.get_template('login.html')
        self.response.write(template.render({}))

    def get_db_obj(self, name):
        query = User.query(User.username == name)
        for item in query:
            return item
        logging.info("-----------------------DB QUERY COULD NOT FIND ANYTHING!___________________")
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

class MainHandler(BaseHandler):
    def get(self):
        loggedin = "You are not logged in"
        str_id = self.get_id()
        if (str_id):
            loggedin = "You are logged in as " + str_id

        template = JINJA_ENVIRONMENT.get_template('homepage.html')
        self.response.write(template.render({'loggedin': loggedin}))
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
        self.send_login_response()

    def post(self):
        email = self.request.get('email').lower()
        username = string.split(email, "@")[0]
        password = self.request.get('password')

        if (authenticate_user.auth_user(username, password)): # Four11 login being finicky, disabled it for now
            expiration_date = datetime.datetime.now()
            obj = {"username": username, "time_issued": expiration_date.isoformat()}
            expiration_date += datetime.timedelta(2) # Cookie should expire in 48 hours

            cookie = base64.b64encode(aes.encryptData(CRYPTO_KEY, json.dumps(obj)))

            self.response.set_cookie('auth', cookie, expires=expiration_date)
            # Now, if user does not already have a database object, make them one
            if not self.get_db_obj(username):
                user = User(username=username)
                for tool_name in TOOLS:
                    setattr(user, tool_name, 0)
                user.put()

            self.response.write("")

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
            resp += "You are currently logged in as " + login + ".Your level on this tool is " + str(getattr(self.get_db_obj(login), tool))
        else:
            resp += "You are not currently logged in. <a href='/login'>LOGIN</a>"

        self.response.write(resp)

class AdminHandler(BaseHandler):
    def post(self):
        admin_name = self.get_id()
        if not admin_name in ADMIN_USERNAMES:
            self.error(403) # Unauthorized
            return

        obj = self.get_db_obj(self.request.get("username"))
        if not obj:
            self.error(400) # Bad request

        for tool_name in TOOLS:
            if self.request.get(tool_name):
                setattr(obj, tool_name, int(self.request.get(tool_name)))

        obj.put()

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', LoginHandler),
    ('/tool/([\w\-]+)', ToolHandler),
    ('/setlevels', AdminHandler)
], debug=True)
