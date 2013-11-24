import os
import urllib
import json

from google.appengine.api import users
from google.appengine.ext import ndb
from operator import itemgetter, attrgetter

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)


"""Datastore Models

"""
ROOT_KEY = ndb.Key('EVENT', 'FAMILY_FUED')

class Wod(ndb.Model):
    """Models a WOD."""
    name = ndb.StringProperty(indexed=True, required=True)
    description = ndb.TextProperty()
    isTimed = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def getWods(cls):
        return cls.query(ancestor=ROOT_KEY).order(cls.name)

    @classmethod
    def getWod(cls, name):
        return cls.query(cls.name == name, ancestor=ROOT_KEY).get()

class Athlete(ndb.Model):
    """Models an athlete."""
    name = ndb.StringProperty(indexed=True, required=True)
    level = ndb.StringProperty(indexed=True, required=True, choices=['Fire Breather', 'Rx', 'Scaled'])

    @classmethod
    def getAthletesByLevel(cls, level):
        return cls.query(cls.level == level).order(cls.name)

    @classmethod
    def getAthleteByNameAndLevel(cls, athleteName, level):
        return cls.query(cls.level == level, cls.name == athleteName).order(cls.name)

    @classmethod
    def getDistinctLevels(cls):
        return cls.query(projection=["level"], distinct=True)

class Score(ndb.Model):
    """An athletes score for a given WOD."""
    athlete = ndb.KeyProperty(kind='Athlete', indexed=True, required=True)
    wod = ndb.KeyProperty(kind='Wod', indexed=True, required=True)
    value = ndb.IntegerProperty(required=True, default=0)

    createdOn = ndb.DateTimeProperty(auto_now_add=True)
    updatedOn = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def getScoresByAthlete(cls, athlete):
        pass

    @classmethod
    def getScoresByWod(cls, wod):
        return cls.query(wod == wod.key).order(cls.value)

    @classmethod
    def getScoresByWodAndAthlete(cls, wod_key, athleteKeyList):
        return cls.query(wod_key == cls.wod, cls.athlete.IN(athleteKeyList)).order(cls.value)

    @staticmethod
    def timeToIntScore(time):
        """For timed scores, take string input like HH:MM:SS"""
        from datetime import datetime, timedelta

        t = datetime.strptime(time, "%H:%M:%S")
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        score = delta.total_seconds()
        return score



#----------------------------------------------------------------------------------------------
# Request Handlers
#----------------------------------------------------------------------------------------------
def getMenuItems(urlBase):
    menuItems = []
    wods = Wod.getWods()
    if not wods: return menuItems
    for wod in wods:
        item = {'name':wod.name, 'url':urlBase % wod.key.id()}
        menuItems.append(item)
    return menuItems

class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {'title': 'Duke City Family Fued', 'wods': getMenuItems('/wod/%s'), 'indexPage': True}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class Admin(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render())


def points_map(rank):
    pts = 100
    while(rank>0):
        pts -= 5
        rank -= 1
    return pts

def sortAndScoreRows(scores):
    sortedScores = sorted(scores, key=attrgetter('value'), reverse=True)

    sortedScoredRows = []
    for rank,score in enumerate(sortedScores):
        sa = {}
        sa['name'] = score.athlete.get().name
        sa['score'] = score.value
        sa['pos'] = rank + 1
        sa['points'] = points_map(rank)
        sortedScoredRows.append(sa)
    return sortedScoredRows 

def createWodResultsTables(levels, wod):
    tables = []
    for level in levels:
        # Find all Athletes in this level
        athletes = Athlete.getAthletesByLevel(level)
        athleteKeyList = [ a.key for a in athletes ]

        # Find all scores for this wod where athletes IN list from step 2
        scores = Score.getScoresByWodAndAthlete(wod.key, athleteKeyList)

        # Based on Score assign each athlete a rank for this Wod, then sort
        rows = sortAndScoreRows(scores)
        table = {'name': level, 'rows': rows}
        tables.append(table)

    return {
        'name': wod.name,
        'tables': tables,
    }

class SingleWodResults(webapp2.RequestHandler):
    def get(self, idval):
        wod = Wod.get_by_id(int(idval), parent=ROOT_KEY)
        if not wod:
            #TODO: Fix this, it doesn't render the error page anymore
            template = JINJA_ENVIRONMENT.get_template('error.html')
            self.response.write(template.render({'msg': 'Wod record not found'}))
            return

        levels = Athlete.getDistinctLevels()
        levels = [ a.level for a in levels ]

        template_values = createWodResultsTables(levels, wod)

        template = JINJA_ENVIRONMENT.get_template('wod.html')
        self.response.write(template.render(template_values))

def reduceScores(wodRankingTables):
    scores = {}
    for wod in wodRankingTables:
        for levelRes in wod:
            # create an object w/ the cat name if necessary or get the one that already exists
            for row in rows:
                # create an athlete object if necessary or inc point count for one that already exists

    return { "fb": [{'name': 'joe', 'points': 10000},
                {'name': 'jim', 'points': 7000},
                ],
             "rx": []
    }
        levelResults = levelRollup.get(level, {'name': })
        levels['name'] = level['name']
        for row in level['rows']:
            athlete = {'name': row['name'],
                    'points': 




class Leaders(webapp2.RequestHandler):
    def get(self):
        levels = Athlete.getDistinctLevels()
        levels = [ a.level for a in levels ]

        wodResults = []
        for wod in wods:
            wodResults.append(createWodResultsTables(levels, wod))

        template_values = reduceWodScores(wodResults)

        template = JINJA_ENVIRONMENT.get_template('wod.html')
        self.response.write(template.render(template_values))


#--------------------------------------------------------------------------------
# Entity Creation Handlers
#--------------------------------------------------------------------------------
class CreateWod(webapp2.RequestHandler):
    def post(self):
        wod = Wod(parent=ROOT_KEY)
        wod.name = self.request.get('wodName')
        wod.description = self.request.get('description')

        type = self.request.get('type')
        if type == 'timed':
            wod.isTimed = True

        wod.put()


        self.redirect('/')

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('create_wod.html')
        self.response.write(template.render())

class CreateAthlete(webapp2.RequestHandler):
    def post(self):
        a = Athlete(parent=ROOT_KEY)
        a.name = self.request.get('athleteName')
        a.level = self.request.get('level')
        a.put()

        self.redirect('/')

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('create_athlete.html')
        self.response.write(template.render())

class CreateScore(webapp2.RequestHandler):
    def post(self):
        s = Score(parent=ROOT_KEY)

        level = self.request.get('level')
        athleteName = self.request.get('athleteName')
        if athleteName and level:
            a = Athlete.getAthleteByNameAndLevel(athleteName, level).get()
            print a
            s.athlete = a.key

        wodName = self.request.get('wod')
        if wodName:
            wod = Wod.getWod(wodName)
            s.wod = wod.key

        score = self.request.get('score')
        print 'score: ' + score
        if  wod.isTimed:
            s.value = Score.timeToIntScore(score)
        else:
            s.value = int(score)

        s.put()

        self.redirect('/')

    def get(self):
        wods = Wod.getWods()
        l = []
        for wod in wods:
            d = {'name': wod.name}
            l.append(d)
        template_values = { 'wods': l }
        template = JINJA_ENVIRONMENT.get_template('create_score.html')
        self.response.write(template.render(template_values))

class FindAthlete(webapp2.RequestHandler):
    def get(self):
        level = self.request.get('level')
        print 'level: ' + level
        
        results = Athlete.getAthletesByLevel(level)

        athletes = []
        for a in results.iter():
            print 'athlete name: ' + a.name
            athletes.append(a.to_dict())
        
        self.response.headers['Content-Type'] = 'application/json'   
        self.response.write(json.dumps(athletes))

#--------------------------------------------------------------------------------
# App configuration
#--------------------------------------------------------------------------------
app = webapp2.WSGIApplication(
        [
            (r'/', MainPage), 
            (r'/wod/(\d+)', SingleWodResults),
            (r'/leaders', Leaders),

            (r'/admin', Admin),
            (r'/admin/createwod', CreateWod),
            (r'/admin/createathlete', CreateAthlete),
            (r'/admin/createscore', CreateScore),

            (r'/athlete', FindAthlete),
        ], 
        debug=True)
