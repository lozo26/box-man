from datetime import date
from itertools import groupby, chain
from operator import setitem, attrgetter

from google.appengine.ext import ndb

from ranking import competitionRanking

"""Datastore Models

"""
# Root for Athletes. They can and should exist outside of an event
ATHLETE_ROOT = ndb.Key('ATHLETE_TABLE', 'DCCF')

# A Division to track training Wods
TRAINING_DIVISION = ndb.Key('Division', 'Training')

# Root for Event.  Parent of Divisions, which exist only for this event.
DEFAULT_EVENT_ROOT = ndb.Key('Event', 'FAMILY_FUED')


class Athlete(ndb.Model):
    """Models an athlete."""
    division = ndb.KeyProperty(indexed=True, required=True)
    name = ndb.StringProperty(indexed=True, required=True)
    email = ndb.StringProperty(indexed=True, required=False)
    dob = ndb.DateProperty(required=False)
    age = ndb.ComputedProperty(lambda self: self._calcAge())

    def _calcAge(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - int((today.month, today.day) < (self.dob.month, self.dob.day))

    def scores(self):
        return Score.query(Score.athlete == self.key).order(Score.wodName).fetch()

    def createScores(self):
        wods = self.division.get().wods
        for wodName in [w.name for w in wods]:
            s = Score(parent=self.division,
                    athlete=self.key, 
                    wodName=wodName,
                    value=0,
                    points=0,
                    rank=0)
            s.put()

    @classmethod
    def all(cls):
        return cls.query(ancestor=ATHLETE_ROOT).fetch()



class Wod(ndb.Model):
    name = ndb.StringProperty(indexed=True, required=True)
    maxPoints = ndb.IntegerProperty(required=True, default=100)
    pointInterval = ndb.IntegerProperty(required=True, default=5)

# prepend with 0_ so that it always sorts BEFORE all other wods
OVERALL_SCORE_WOD = "0_OVERALL_DIVSION_SCORE_WOD"
class Division(ndb.Model):
    """Models a competition division.
    
        Currently the wods are stored as structure properties which means they don't have
        keys of their own in the store.  This could have implications for data integrity.
        I.e. misspelling a wod could un-intentionally create a new one rather than update
        records associated with an existing.

        One solution to this would be to make wods a repeated KeyProperty instead where
        each wod is stored as its own entity w/ Division as it's parent.  This however,
        might require an additional step when querying for Score records by division
        and wod since we'd need the key for both.  This may not be that bad or I could
        potentially figure out a way to avoid this but don't want to spend the time on it
        right now.
    """
    name = ndb.StringProperty(indexed=True, required=True)
    wods = ndb.StructuredProperty(Wod, repeated=True)
    athletes = ndb.KeyProperty(Athlete, repeated=True)

    @classmethod
    def all(cls, event=DEFAULT_EVENT_ROOT):
        return cls.query(ancestor=event).fetch()

    def athletes(self):
        return Athlete.query(Athlete.division == self.key)

    def athleteOverallScore(self, athlete_key):
        """Returns the single record for this athletes overall score in the division."""
        return Score.query(Score.athlete == athlete_key, Score.wodName == OVERALL_SCORE_WOD, ancestor=self.key).get()

    def athleteScores(self, athlete_key):
        """Returns all scores for this athletes in the division."""
        return Score.query(Score.athlete == athlete_key, Score.wodName != OVERALL_SCORE_WOD, ancestor=self.key)

    def wodScores(self, wodName=OVERALL_SCORE_WOD):
        """Returns all scores for the wod in this division, with the given wod name."""
        return Score.query(Score.wodName == wodName, ancestor=self.key)

    def rankWod(self, wodName):
        wod = next(wod for wod in self.wods if wod.name == wodName)
        scores = self.wodScores(wodName).fetch()
        self._rank(scores)
        for s in scores:
            s.points = wod.maxPoints - (s.rank - 1) * wod.pointInterval
            s.put()

    def rankAll(self):
        scores = self.wodScores().fetch() # scores for overall
        for score in scores: # update overall by re-summing athletes scores for all wods
            athlete_scores = self.athleteScores(score.athlete).fetch()
            score_sum = 0
            for s in athlete_scores: # sum wod points
                score_sum += s.points
            score.points = score_sum
            score.value = score_sum
        self._rank(scores) # set rankings
        for s in scores: # save changes
            s.put()

    def _rank(self, scores):
        sortedScores = sorted(scores, key=attrgetter('value'), reverse=True)
        groups = groupby(sortedScores, key=attrgetter('value'))
        competitionRanking(groups, lambda s, rank: setattr(s, 'rank', rank))


class Score(ndb.Model):
    """An athletes score for a given WOD in a particular Division.
    
       The Division for this Score will be the Parent.
    """
    athlete = ndb.KeyProperty(kind='Athlete', indexed=True, required=True)
    wodName = ndb.StringProperty()

    # Set by user
    value = ndb.IntegerProperty(required=True, default=0)
    isTimeValue = ndb.BooleanProperty(required=True, default=False)

    # Computed based on scores grouped by division and wod
    rank = ndb.IntegerProperty(required=False)
    points = ndb.IntegerProperty(required=False)

    # for posterity, to track who is modifying the scores and when
    createdOn = ndb.DateTimeProperty(auto_now_add=True)
    updatedOn = ndb.DateTimeProperty(auto_now=True)
    #updatedBy = ndb.UserProperty() # is there a way to automatically set this?

    @classmethod
    def all(cls, division=TRAINING_DIVISION):
        return cls.query(ancestor=division).fetch()



    @staticmethod
    def timeToIntScore(time):
        """For timed scores, take string input like HH:MM:SS"""
        from datetime import datetime, timedelta

        t = datetime.strptime(time, "%H:%M:%S")
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        return int(delta.total_seconds())

