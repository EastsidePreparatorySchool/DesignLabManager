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
TOOLS = ["vinyl_cutter", "power_tools", "sewing_machine", "hand_tools", "lasers", "cnc", "printers_3d", "soldering", "coffee_maker"]
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
    power_tools = ndb.IntegerProperty()
    lasers = ndb.IntegerProperty()
    cnc = ndb.IntegerProperty()
    printers_3d = ndb.IntegerProperty()
    soldering = ndb.IntegerProperty()
    coffee_maker = ndb.IntegerProperty()

class BaseHandler(webapp2.RequestHandler):
    def open_html(self, filepath):
        with open(filepath, 'r') as f:
            data = f.read()
        return data
        
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

    def db_user_to_simple_obj(self, db_obj):
        obj = {"username" : db_obj.username}
        for tool in TOOLS:
            attr = getattr(db_obj, tool)
            obj[tool + "_cert"] = attr
        return obj

class MainHandler(BaseHandler):
    def get(self):
        loggedin = "You are not logged in"
        logincomps = self.open_html('logincomponents.html')

        loginmodal = self.open_html('modal.html')

        str_id = self.get_id()
        if (str_id):
            loggedin = "You are logged in as " + str_id
            logincomps = '<a href="logout">--Log Out--</a>'

        
        template = JINJA_ENVIRONMENT.get_template('homepage.html')
        self.response.write(template.render({'loggedin': loggedin, 'loginURL': logincomps, 'loginmodal': loginmodal}))
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
        if "@" not in email:
            email += "@eastsideprep.org"
        password = self.request.get('password')

        if (authenticate_user.auth_user(email, password)): # Four11 login being finicky, disabled it for now
            username = string.split(email, "@")[0] 
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

class LogoutHandler(BaseHandler):
    def get(self):
        self.response.delete_cookie("auth")
        self.redirect("/")

class ToolHandler(BaseHandler):
    def get(self, tool):
        if tool not in TOOLS:
            self.error(404)
            return

        template = JINJA_ENVIRONMENT.get_template('/tool_pages/' + tool + '.html')
        self.response.write(template.render({}))

class AdminHandler(BaseHandler):
    def get(self):
        admin_name = self.get_id()
        if not admin_name in ADMIN_USERNAMES:
            self.error(403) # Unauthorized
            return

        # Generate HTML for all students

        query = User.query() # Get all students
        rows = ""
        for student in query:
            row = JINJA_ENVIRONMENT.get_template('studentrow.html')
            rows += row.render(self.db_user_to_simple_obj(student))

        template = JINJA_ENVIRONMENT.get_template('admin.html')

        self.response.write(template.render({'students' : rows}))

class AdminUserSearchHandler (BaseHandler):
    def post(self):
        admin_name = self.get_id()
        if not admin_name in ADMIN_USERNAMES:
            self.error(403) # Unauthorized
            return

        username = self.request.get("username")
        username = string.split(username, "@")[0] # Turn emails to usernames

        obj = self.get_db_obj(username)
        if not obj:
            self.response.write("That user has never logged in.")
        if not obj.username:
            self.response.write("That user has never logged in.")

        self.response.write("/userlevel/" + username)

class DataViewHandler(BaseHandler):
    def get(self, username):
        admin_name = self.get_id()
        if not admin_name in ADMIN_USERNAMES:
            self.error(403) # Unauthorized
            return

        template = JINJA_ENVIRONMENT.get_template('admin_view.html')
        self.response.write(template.render(self.db_user_to_simple_obj(self.get_db_obj(username))))

class LevelSetHandler (BaseHandler):
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
    ('/admin', AdminHandler),
    ('/getuser', AdminUserSearchHandler),
    ('/userlevel/([\w\-]+)', DataViewHandler),
    ('/setlevel', LevelSetHandler),
    ('/logout', LogoutHandler)
], debug=True)
