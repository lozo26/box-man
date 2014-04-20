import os
import json
import pprint
from operator import itemgetter, attrgetter

import jinja2
import webapp2
from webapp2_extras import routes

from google.appengine.api import users
from google.appengine.ext import ndb

from models import *

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)
JINJA_ENVIRONMENT.globals['uri_for'] = webapp2.uri_for

#----------------------------------------------------------------------------------------------
# User Interface Request Handlers
#----------------------------------------------------------------------------------------------
class MainPage(webapp2.RequestHandler):
    def get(self, div_key=None):
        divisions = Division.all()
        template_values = { 
                'divisions': divisions,
        }

        if div_key:
            wodNames, tbl = self._score_data(div_key)
            template_values['wodNames'] = wodNames
            template_values['score_tbl'] = tbl
            template_values['sel_division'] = True

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

    def get_leaders(self, div_key):
        wodNames, tbl = self._score_data(div_key)
        template_values = { 
                'wodNames': wodNames,
                'score_tbl': tbl
        }
        template = JINJA_ENVIRONMENT.get_template('leaders.html')
        self.response.write(template.render(template_values))

    def _score_data(self, div_key):
        div = ndb.Key(urlsafe=div_key).get()
        wodNames = [wod.name for wod in div.wods]
        ovrall = div.wodScores().order(Score.rank).fetch()
        tbl = []
        for o in ovrall:
            row = []
            row.append(div.athleteOverallScore(o.athlete))
            row.extend(div.athleteScores(o.athlete).fetch())
            tbl.append(row)
        return (wodNames, tbl)


class Admin(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render())

#--------------------------------------------------------------------------------
# Entity Admin Handlers
#--------------------------------------------------------------------------------
class AthleteHandler(webapp2.RequestHandler):
    def show(self):
        template = JINJA_ENVIRONMENT.get_template('athletes.html')
        self.response.write(template.render({ 'athletes':Athlete.all() }))

    def save(self):
        key = self.request.get('id') # hidden id field
        name = self.request.get('name')
        div_key = self.request.get('division')
        email = self.request.get('email')
        month = self.request.get('dob_MM')
        day = self.request.get('dob_DD')
        year = self.request.get('dob_YYYY')

        if key:     # edit
            a_key = ndb.Key(urlsafe=key)
            a = a_key.get()
        else:       # create
            a = Athlete(parent=ATHLETE_ROOT)

        a.name = name
        a.division = ndb.Key(urlsafe=div_key)
        a.email = email
        if month and day and year:
            a.dob = date(int(year), int(month), int(day))
        a.put()

        if not key: # create new score for each wod 
            a.createScores()

        self.redirect_to('show-athletes')

    def create(self):
        template = JINJA_ENVIRONMENT.get_template('create_athlete.html')
        self.response.write(template.render({'divisions': Division.all()}))

    def edit(self, key):
        ath_key = ndb.Key(urlsafe=key)
        ath = ath_key.get()
        template_values = {
                'id': key,
                'name': ath.name,
                'email': ath.email,
                'dob_mm': ath.dob.month,
                'dob_dd': ath.dob.day,
                'dob_yyyy': ath.dob.year,
        }
        template = JINJA_ENVIRONMENT.get_template('create_athlete.html')
        self.response.write(template.render(template_values))

    def delete(self, key):
        ndb.Key(urlsafe=key).delete()
        self.redirect_to("show-athletes")
        

class DivisionHandler(webapp2.RequestHandler):
    def show(self):
        template = JINJA_ENVIRONMENT.get_template('divisions.html')
        self.response.write(template.render({ 'divisions':Division.all() }))

    def save(self):
        key = self.request.get('id') # hidden id field
        name = self.request.get('name')
        wodNames = self.request.get_all('wodname')
        maxPoints = self.request.get_all('maxPoints')
        pointIntervals = self.request.get_all('pointInterval')
        
        if key:     # edit
            d_key = ndb.Key(urlsafe=key)
            d = d_key.get()
        else:       # create
            d = Division(parent=DEFAULT_EVENT_ROOT)

        d.name = name
        for w_name, maxpts, interval in zip(wodNames, maxPoints, pointIntervals):
            d.wods.append(Wod(name=w_name,
                maxPoints=int(maxpts),
                pointInterval=int(interval)))
        d.put()

        self.redirect_to('show-divisions')

    def create(self):
        template = JINJA_ENVIRONMENT.get_template('create_division.html')
        self.response.write(template.render())

    def edit(self, key):
        d_key = ndb.Key(urlsafe=key)
        division = d_key.get()
        template_values = {
                'id': key,
                'name': division.name,
        }
        template = JINJA_ENVIRONMENT.get_template('create_division.html')
        self.response.write(template.render(template_values))

    def delete(self, key):
        ndb.Key(urlsafe=key).delete()
        self.redirect_to("show-divisions")


"""
Wod Ranking and Scoring Algorithm:
    - Get all scores for a given wod/division combo
    - Sort by Score.value
    - Assign Rank based on sorted order
    - Assign points based on Rank and wod.maxPoints and wod.pointInterval values

Score Update Mechanism:
    - Each time a score is entered, recalculate and set the rankings and points for that score's Div/Wod combo
    - After recalculating the Div/Wod points, recalculate the overall Div points
        * Overall scores will be treated like another Wod with the following caveats:
            - value = this will be the same value of points (see below)
            - wodName = OVERALL_SCORE # a constant defined in models.py
            - points = Ignored.  We're using value instead
            - rank will be cacluated just as all other wods which is why the point summation MUST
              be stored in teh value field rather than the points field
        * Special case will have to be made to display the OVERALL wod since value and point
          fields will have slightly different meanings than for normal wods

    PROS:
        * Rankings will always be up to date when new scores entered.
        * Don't have to worry about unintentionally having outdated/incorrect rankings
    CONS:
        * Rankings are recalculated several times.

    Analysis:
        Although rankings are done repeatedly, the datasets are small enough that the calculation should still be 
        relatively fast.  Even if the calculation is slow by computational standards, it only has to be fast enough
        to be done by the time the user enters the next score.  Given that a user could only enter scores on the order
        of one in several seconds, and the rankings calculation should be done in well under a second for the anticipated
        data sets, this design should be fine.

        If ever it became an issue such that ranking calculations started to take approach times ~1sec or greater, then
        modifications to this system would be required to adhere to GAE's infrustructure optimizations and to address
        likely usability concerns (users don't like to wait).  The likely solution in this case would be to simply allow
        scores to be entered as quickly as a user could input them (potentially multiple users).  Then fire off a job
        to caclulate the rankings based on some trigger which could be manual (user clicks a button) or automated
        (set to go off at a time when score entry is no longer ongoing).
"""
class ScoreHandler(webapp2.RequestHandler):
    def update(self):
        score_key = self.request.get('pk')
        name = self.request.get('name')
        value = self.request.get('value')

        score = ndb.Key(urlsafe=score_key).get()
        if ':' in value: #time value
            score.value = Score.timeToIntScore(value)
            score.isTimeValue = True
        else:
            score.value = int(value)
        score.put()
        div_key = score.key.parent()

        # Do ranking/scoring
        div = div_key.get()
        div.rankWod(score.wodName) 
        div.rankAll()

        self.redirect_to('edit-scores', div_key=div_key.urlsafe())

    def _score_entry_data(self, div_key):
        div = ndb.Key(urlsafe=div_key).get()
        wodNames = sorted([wod.name for wod in div.wods]) # sort by wod name
        athletes = div.athletes().order(Athlete.name).fetch()
        tbl = []
        for a in athletes:
            row = []
            row.extend(div.athleteScores(a.key).order(Score.wodName).fetch()) # get scores also sorted by wod name
            tbl.append(row)
        return (wodNames, tbl)

    def edit(self, div_key=None):
        divisions = Division.all()
        template_values = { 
                'divisions': divisions,
        }

        if div_key:
            wodNames, tbl = self._score_entry_data(div_key)
            template_values['wodNames'] = wodNames
            template_values['score_tbl'] = tbl
            template_values['sel_division'] = True

        template = JINJA_ENVIRONMENT.get_template('scoring.html')
        self.response.write(template.render(template_values))

    def get_div_scores(self, div_key):
        wodNames, tbl = self._score_entry_data(div_key)
        print wodNames
        print tbl
        template_values = { 
                'wodNames': wodNames,
                'score_tbl': tbl
        }
        template = JINJA_ENVIRONMENT.get_template('score_entry.html')
        self.response.write(template.render(template_values))


#--------------------------------------------------------------------------------
# App configuration
#--------------------------------------------------------------------------------
app = webapp2.WSGIApplication(
        [
            (r'/', MainPage), 
            webapp2.Route(r'/leaders/<div_key:[A-Za-z0-9_-]+>', MainPage, 'get-leaders', handler_method='get_leaders', methods=['GET']),


            (r'/admin', Admin),

            routes.PathPrefixRoute('/admin/create', [
                webapp2.Route('/athlete', AthleteHandler, 'create-athlete', handler_method='create', methods=['GET']),
                webapp2.Route('/athlete', AthleteHandler, 'save-athlete', handler_method='save', methods=['POST']),

                webapp2.Route('/division', DivisionHandler, 'create-division', handler_method='create', methods=['GET']),
                webapp2.Route('/division', DivisionHandler, 'save-division', handler_method='save', methods=['POST']),
            ]),

            routes.PathPrefixRoute('/admin/edit', [
                webapp2.Route('/athlete/<key:[A-Za-z0-9_-]+>', AthleteHandler, 'edit-athlete', handler_method='edit', methods=['GET']),
                webapp2.Route('/division/<key:[A-Za-z0-9_-]+>', DivisionHandler, 'edit-division', handler_method='edit', methods=['GET']),

                webapp2.Route(r'/score', ScoreHandler, 'update-score', handler_method='update', methods=['POST']),
                webapp2.Route(r'/scores', ScoreHandler, 'edit-scores', handler_method='edit', methods=['GET']),
                webapp2.Route(r'/scores/<div_key:[A-Za-z0-9_-]+>', ScoreHandler, 'get-div-scores', handler_method='get_div_scores', methods=['GET']),
            ]),

            routes.PathPrefixRoute('/admin/show', [
                webapp2.Route('/athletes', AthleteHandler, 'show-athletes', handler_method='show', methods=['GET']),
                webapp2.Route('/divisions', DivisionHandler, 'show-divisions', handler_method='show', methods=['GET']),
            ]),

            routes.PathPrefixRoute('/admin/delete', [
                webapp2.Route('/athlete/<key:[A-Za-z0-9_-]+>', AthleteHandler, 'delete-athlete', handler_method='delete', methods=['GET']),
                webapp2.Route('/division/<key:[A-Za-z0-9_-]+>',  DivisionHandler, 'delete-division', handler_method='delete', methods=['GET']),
            ]),
        ], 
        debug=True)
