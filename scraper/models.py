from sqlalchemy import Column, String, Float, Integer, Interval
from sqlalchemy.ext.declarative import declarative_base
import datetime
from scraper.datatypes import UTCDateTime

Base = declarative_base()


# specific entries for the most recent calculated rate for the particular posting
class Rate(Base):
    __tablename__ = 'rates'

    # the thing id like 't3_78n7ni'
    submission_id = Column(String(length=9), primary_key=True)
    # the rate in comments / minute
    rate = Column(Float, nullable=False)
    # can i auto set this somehow
    timestamp = Column(UTCDateTime, nullable=False)
    created = datetime.datetime

# counts of comments at various times
class Tracker(Base):
    __tablename__ = 'tracker'

    submission_id = Column(String(length=9), primary_key=True)
    comment_count = Column(Integer, nullable=False)
    # TODO: this default doesn't work. it gets set at start up and is constant. no good.
    timestamp = Column(UTCDateTime, nullable=False, default=datetime.datetime.utcnow())


# represents the peak comment rate that a certain thread hits
# useful to analyse trends
class PeakRate(Base):
    __tablename__ = 'peak_rates'

    # the thing id...
    submission_id = Column(String(length=9), primary_key=True)
    # the rate
    rate = Column(Float, nullable=False)
    # amount of time that occured until this post hit its peak rate
    time_since_creation = Column(Interval, nullable=False)
