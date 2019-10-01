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



ADMIN_USERNAMES = ["guberti", "qbowers", "jbriggs", "dclarke", "jnolan", "msudo", "dmulye","shollingshead", "dyezbick","jdenhart"]
TOOLS = ["vinyl_cutter", "power_tools", "sewing_machine", "hand_tools", "lasers", "cnc", "printers_3d", "soldering", "coffee_maker"]
TOOL_FULL_NAMES = ["vinyl cutter", "power tools", "sewing machine", "hand tools", "laser cutters", "ShopBot", "3D printers", "soldering iron", "coffee maker"]
CRYPTO_KEY = open('data/crypto.key', 'rb').read()

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    vinyl_cutter = ndb.IntegerProperty(default=0)
    power_tools = ndb.IntegerProperty(default=0)
    sewing_machine = ndb.IntegerProperty(default=0)
    hand_tools = ndb.IntegerProperty(default=0)
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
        try:
            decoded = aes.decryptData(CRYPTO_KEY, base64.b64decode(cookie))
        except TypeError:
            return None
        return json.loads(decoded)["username"]

    def is_admin(self):
        if (self.get_id()):
            if (self.get_id() in ADMIN_USERNAMES):
                return True
        return False

    def get_db_obj(self, username):
        return ndb.Key('User', username).get(use_cache=False, use_memcache=False)

    def new_db_obj(self, username):
        user = User(username=username)
        user.key = ndb.Key('User', username)
        user.put()

    def db_user_to_simple_obj(self, db_obj):
        obj = {"username" : db_obj.username}
        for tool in TOOLS:
            attr = getattr(db_obj, tool)
            obj[tool] = attr
        return obj

    def get_levels(self, id):
        db_obj = self.get_db_obj(id)
        obj = self.db_user_to_simple_obj(db_obj)
        return obj

    def get_levels_verbose(self, id):
        obj = self.get_levels(id)
        v_obj = {}
        for i in range(0, len(TOOLS)):
            v_obj[TOOL_FULL_NAMES[i]] = obj[TOOLS[i]]
        return v_obj

    def send_template(self, path, options):
        template = JINJA_ENVIRONMENT.get_template(path)
        if (self.get_id()):
            options["user"] = self.get_id()
        options["admin"] = self.is_admin()
        options["tools"] = TOOL_FULL_NAMES
        self.response.write(template.render(options))

class MainHandler(BaseHandler):
    def get(self):

        #self.new_db_obj('nbowers')

        user = False
        values = {}
        str_id = self.get_id()

        if (str_id):
            obj = self.get_db_obj(str_id)
            values.update(self.db_user_to_simple_obj(obj))
            values['total_certs'] = User.query().count()

        self.send_template('public/index.html', values)


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
        values = {}
        str_id = self.get_id()

        if (str_id):
            obj = self.get_db_obj(str_id)
            level = getattr(obj, tool)
            if not level:
                str_id = None # Simply triggers the default case below. Does NOT delete user from database
            else:
                values['cert_num'] = 'You are certified to level ' + str(level) + '.'

        if not (str_id):
            values['cert_num'] = 'Join the ' + str(total_certified) + ' people certified by talking to Mr. Mack.'

        for i in range(1, 6):
            values['level_' + str(i)] = User.query(User._properties[tool] == i).count()

        self.send_template('public/tool/' + tool + '.html', values)



class NewAdminHandler(BaseHandler):
    def get(self):
        if not (self.is_admin()):
            self.error(403)
            return

        #logging.info('------------' + self.get_id())
        levels = self.get_levels_verbose(self.get_id())
        self.send_template('public/new_admin.html', {'levels': levels})

class AdminDataHandler(BaseHandler):
    def get(self):
        userrequest = True
        #logging.info('\n\n-----------------------ADMIN DATA--------------------------\n\n')
        if not (self.is_admin()):
            self.error(403)
            return
        if not (self.request.get('user')):
            userrequest = False
            if not (self.request.get('tool')):
                self.error(404)
                return

        data = {}
        if (userrequest):
            data = {'user': self.request.get('user'), 'levels': self.userData(self.request.get('user').lower())}
        else:
            data = self.toolData(self.request.get('tool').lower())

        #self.response.headers['content-type'] = 'application/json'
        self.response.out.write(json.dumps(data))

    def userData(self, user):
        return self.get_levels_verbose(user)
    def toolData(self, tool):
        users = [];
        query = User.query(User.printers_3d > 0)
        for user in User.query():
            obj = self.db_user_to_simple_obj(user)

            #obj.username == null
            #users.append({'username': obj.username, level: obj[tool]})
            users.append({'username': obj})
        return {
            'tool': tool,
            'users': users
        }

    def post(self):
        if not (self.is_admin()):
            self.error(403)
            return
        if not (self.request.get('user')):
            self.error(404)
            return
        if not self.request.get('tool') in TOOL_FULL_NAMES:
            self.error(404)
            return

        user = self.request.get('user').lower()
        if not (self.get_db_obj(user)):
            self.error(404)
            return
        tool_full = self.request.get('tool')
        tool = TOOLS[TOOL_FULL_NAMES.index(tool_full)]

        obj = self.get_db_obj(user)
        setattr(obj, tool, int(self.request.get('level')))
        obj.put()
        self.response.write('')


class AdminHandler(BaseHandler):
    def get(self):
        admin_name = self.get_id()
        if not admin_name in ADMIN_USERNAMES:
            self.error(403) # Unauthorized
            return

        # Generate HTML for all students

        query = User.query() # Get all students
        rows = ""


        logging.info('\n\n\n------------------------------------------\n\n\n')
        row = JINJA_ENVIRONMENT.get_template('public/studentrow.html')
        for student in query:
            rows += row.render(self.db_user_to_simple_obj(student))

        ##Replace new_admin.html with admin.html for practical purposes
        self.send_template('public/admin.html', {'students' : rows})

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
            if not bool(self.request.get("create")):
                self.response.write("That user has never logged in.")
                return
            else:
                self.new_db_obj(username)
                # We'll return a URL at the end

        if not obj.username:
            self.response.write("That user has never logged in.")
            return

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
                logging.info(tool_name)
                setattr(obj, tool_name, int(self.request.get(tool_name)))

        obj.put()

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', LoginHandler),
    ('/tool/([\w\-]+)', ToolHandler),
    #('/admin', NewAdminHandler),
    ('/admin', AdminHandler),
    ('/admin/data', AdminDataHandler),
    ('/getuser', AdminUserSearchHandler),
    ('/userlevel/([\w\-]+)', DataViewHandler),
    ('/setlevel', LevelSetHandler)
], debug=True)
