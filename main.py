#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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

def load_json_file(filename, has_test_data = False):
    return json.load(open_data_file(filename, has_test_data))

def create_error_obj(error_message):
    error_obj = {"error":error_message}
    return json.dumps(error_obj)

with open('id_table.json') as data_file:    
    ID_TABLE = json.load(data_file)
ADMIN_IDS = [106, 4469, 4340, 4348, 4093, 4441]
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class User(ndb.Model):
    sid = ndb.IntegerProperty(required=True)
    fullname = ndb.StringProperty()
    vinyl_cert_level = ndb.IntegerProperty()
    sewing_machine_cert_level = ndb.IntegerProperty()
    tools_cert_level = ndb.IntegerProperty()
    epilog_cert_level = ndb.IntegerProperty()
    universal_laser_cert_level = ndb.IntegerProperty()
    cnc_cert_level = ndb.IntegerProperty()
    printrbot_cert_level = ndb.IntegerProperty()
    robo3d_cert_level = ndb.IntegerProperty()
    soldering_cert_level = ndb.IntegerProperty()
    coffee_maker_cert_level = ndb.IntegerProperty()

class Use(ndb.Model):
    sid = ndb.IntegerProperty(required=True)
    start_time = ndb.DateTimeProperty()
    machine = ndb.StringProperty()
    material = ndb.StringProperty()
    project = ndb.StringProperty()

class BaseHandler(webapp2.RequestHandler):
    def get_id(self):
        return self.request.cookies.get("SID")

    def send_login_response(self):
        template = JINJA_ENVIRONMENT.get_template('login.html')
        self.response.write(template.render({}))

    def convert_email_to_id(self, email):
        email = email.lower()
        pieces = string.split(email, "@")
        username = pieces[0]
        for student in ID_TABLE:
            if (student[0] == username):
                return student[1]
        return None

    def db_user_to_simple_obj(self, obj):
        return {
            'sid': obj.sid,
            'fullname': obj.fullname,
            'vinyl_cert_level': obj.vinyl_cert_level,
            'sewing_machine_cert_level': obj.sewing_machine_cert_level,
            'epilog_cert_level': obj.epilog_cert_level,
            'universal_laser_cert_level': obj.universal_laser_cert_level,
            'cnc_cert_level': obj.cnc_cert_level,
            'printrbot_cert_level': obj.printrbot_cert_level,
            'robo3d_cert_level': obj.robo3d_cert_level,
            'soldering_cert_level': obj.soldering_cert_level,
            'tools_cert_level': obj.tools_cert_level,
            'coffee_maker_cert_level': obj.coffee_maker_cert_level
        };

class MainHandler(BaseHandler):
    def get(self):
        str_id = self.get_id()
        if not str_id:
            self.send_login_response()
            return
        user_id = int(str_id)

        query = User.query(User.sid == user_id)
        for db_obj in query: # Will only ever be one
            template_values = { \
            'sid': db_obj.sid, \
            'fullname': db_obj.fullname, \
            'sewing_machine_cert_level': db_obj.sewing_machine_cert_level, \
            'soldering_cert_level': db_obj.soldering_cert_level, \
            }
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
            break

class LoginHandler(BaseHandler):
    def post(self):
        email = self.request.get('email').lower()
        user_id = self.convert_email_to_id(email)
        expiration_date = datetime.datetime.now()
        expiration_date += datetime.timedelta(3650) # Set expiration date 10 years in the future
        self.response.set_cookie('SID', str(user_id), expires=expiration_date)

        self.response.write(create_error_obj(""))
        logging.info("Wrote a response!")

class AdminHandler(BaseHandler):
    def get(self):
        str_id = self.get_id()
        if not str_id:
            self.send_login_response()
            return
        user_id = int(str_id)

        if not user_id in ADMIN_IDS:
            self.response.write("You are not an admin!")

        entriesQuery = User.query()
        entries = []
        for obj in entriesQuery:
            entries.append(self.db_user_to_simple_obj(obj))

        logging.warning(json.dumps(entries))

        template_values = { \
            'entries': json.dumps(entries) \
        }
        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render(template_values))

class AddDataHandler(BaseHandler):
    def get(self):
        for student in ID_TABLE:
            query = User.query(User.sid == student[1])
            has_obj = False
            for obj in query:
                has_obj = True
                break

            if has_obj:
                continue

            user_obj = User(
                sid = student[1],
                fullname = student[0],
                sewing_machine_cert_level = 0,
                soldering_cert_level = 0,
                vinyl_cert_level = 0,
                epilog_cert_level = 0,
                universal_laser_cert_level = 0,
                cnc_cert_level = 0,
                printrbot_cert_level = 0,
                robo3d_cert_level = 0,
                tools_cert_level = 0,
                coffee_maker_cert_level = 0
            )
            user_obj.put()
            logging.info("Added " + student[0] + " to the database")
        self.response.write('Success!!')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/adddata', AddDataHandler),
    ('/login', LoginHandler),
    ('/admin', AdminHandler)
], debug=True)
