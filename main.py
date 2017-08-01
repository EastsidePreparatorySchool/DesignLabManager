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
TOOL_FULL_NAMES = ["the vinyl cutter", "power tools", "the sewing machine", "hand tools", "the laser cutters", "the ShopBot", "the 3D printers", "soldering", "making coffee"]
CRYPTO_KEY = open('data/crypto.key', 'rb').read()

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    vinyl_cutter = ndb.IntegerProperty(default=0)
    sewing_machine = ndb.IntegerProperty(default=0)
    hand_tools = ndb.IntegerProperty(default=0)
    power_tools = ndb.IntegerProperty(default=0)
    lasers = ndb.IntegerProperty(default=0)
    cnc = ndb.IntegerProperty(default=0)
    printers_3d = ndb.IntegerProperty(default=0)
    soldering = ndb.IntegerProperty(default=0)
    coffee_maker = ndb.IntegerProperty(default=0)

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

    def get_db_obj(self, username):
        return ndb.Key('User', username).get()
        return None

    def new_db_obj(self, username):
        user = User(username=username)
        user.key = ndb.Key('User', username)
        user.put()

    def db_user_to_simple_obj(self, db_obj):
        obj = {"username" : db_obj.username}
        for tool in TOOLS:
            attr = getattr(db_obj, tool)
            obj[tool + "_cert"] = attr
        return obj

    def send_template(self, path, options):
        template = JINJA_ENVIRONMENT.get_template(path)
        if (self.get_id()):
            options["user"] = self.get_id()
        self.response.write(template.render(options))

class MainHandler(BaseHandler):
    def get(self):
        levelKeys = ["noviceLevels", "competentLevels", "proficientLevels", "advancedLevels", "expertLevels"]
        levelNames = ["a novice", "competent", "proficient", "advanced", "an expert"]

        prefix = "You are proficient on "

        levelReplacements = ["", "", "", "", ""]
        values = {}


        user = False

        values = {}

        str_id = self.get_id()
        if (str_id):
            obj = self.get_db_obj(str_id)

            values.update(self.db_user_to_simple_obj(obj))

            for i in range (0, len(levelKeys)):
                values[levelKeys[i]] = "You are " + levelNames[i] + " on " + self.getToolsAtLevel(obj, i + 1)
            user = str_id


        self.send_template('public/index.html', values)


    def getToolsAtLevel(self, obj, level):
        t = []
        for i in range (0, len(TOOLS)):
            if getattr(obj, TOOLS[i]) == level:
                t.append(TOOL_FULL_NAMES[i])

        if len(t) == 0:
            return "nothing."
        if len(t) == 1:
            return t[0] + "."

        s = ""
        for i in range (0, len(t)):
            s += t[i]
            if i != (len(t) - 1):
                s += ", "
            if i == (len(t) - 2):
                s += "and "

        s += "."

        return s

class LoginHandler(BaseHandler):
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
                self.new_db_obj(username)


            self.response.write("")

        else:
            self.response.write("Username or password was incorrect")

class ToolHandler(BaseHandler):
    def get(self, tool):
        if tool not in TOOLS:
            self.error(404)
            return

        total_certified = User.query(User._properties[tool] > 0).count()
        people_certified_by_level = []

        values = {'total_certified': total_certified}

        for i in range(1, 6):
            values['level_' + str(i)] = User.query(User._properties[tool] == i).count()

        self.send_template('public/tool/' + tool + '.html', values)


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
            row = JINJA_ENVIRONMENT.get_template('public/studentrow.html')
            rows += row.render(self.db_user_to_simple_obj(student))

        ##Replace new_admin.html with admin.html for practical purposes
        #template = JINJA_ENVIRONMENT.get_template('public/new_admin.html')

        #self.response.write(template.render({'students' : rows}))
        self.send_template('public/new_admin.html', {'students' : rows})

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

        template = JINJA_ENVIRONMENT.get_template('public/admin_view.html')
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
    ('/setlevel', LevelSetHandler)
], debug=True)
