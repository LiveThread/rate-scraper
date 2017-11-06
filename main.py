import praw
from models import Tracker, Rate, PeakRate, Base

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timezone, timedelta
import time
import config

# init stuff
db = create_engine(config.db_connection)

# TOOD: does this drop if exists?
Base.metadata.create_all(db)
print("all tables created.")

reddit = praw.Reddit(client_id=config.reddit_client_id,
                     client_secret=None,
                     user_agent='hot comment thread calculator',
                     implicit=True)

DBSession = sessionmaker(bind=db)
session = DBSession()


def get_subreddits():
    """
    :return: Read in the lines from subreddits.txt and return the list of subreddits to traverse
    """
    f = open("subreddits.txt", "r")
    subreddits = []
    for line in f:
        if line.startswith('#'):
            continue
        if line == "\n":
            continue
        subreddits.append(line.rstrip('\n'))
    return subreddits


# run until dead...
# TODO: would chron be more appropriate?
# TODO: clean this up / break it into functions
while True:
    start = time.time()
    print(datetime.now(timezone.utc))
    # make sure we are clear
    session.commit()

    # get the posts from all the subreddits
    posts = []
    for sub_name in get_subreddits():
        print('fetching "' + sub_name + '"')
        posts.extend(reddit.subreddit(sub_name).hot(limit=5))

    new_entries = []
    for post in posts:
        # if post older than 36 hours ignore it
        post_timestamp = datetime.fromtimestamp(post.created_utc, timezone.utc)
        current_timestamp = datetime.now(timezone.utc)

        if (current_timestamp - post_timestamp) > timedelta(hours=36):
            continue

        print(post.fullname)
        print(post.title)
        entry = Tracker(submission_id=post.fullname, comment_count=post.comments.__len__(),
                        timestamp=current_timestamp)
        entry.created = post_timestamp
        new_entries.append(entry)
        # session.add(entry)

    session.commit()

    for entry in new_entries:
        last_entry = session.query(Tracker).filter(Tracker.submission_id == entry.submission_id)
        if last_entry.count() != 1:
            print("does not yet exist in db")
            session.add(entry)
            continue
        old = last_entry[0]
        new = entry
        comment_diff = new.comment_count - old.comment_count
        # in minutes
        time_diff = (new.timestamp - old.timestamp).total_seconds() / 60

        # proper behavior?
        if comment_diff < 0:
            continue

        print("time_diff " + str(time_diff))
        print("new comment count: " + str(new.comment_count))
        print("old comment count: " + str(old.comment_count))
        print(comment_diff)

        old.comment_count = new.comment_count
        old.timestamp = new.timestamp

        rate_entries = session.query(Rate).filter(Rate.submission_id == entry.submission_id)
        rate_entry = Rate()
        if rate_entries.count() > 0:
            rate_entry = rate_entries[0]
            rate_entry.rate = comment_diff / time_diff
            rate_entry.timestamp = datetime.now(timezone.utc)
        else:
            rate_entry = Rate(submission_id=entry.submission_id, rate=comment_diff / time_diff,
                              timestamp=datetime.now(timezone.utc))
            session.add(rate_entry)

        # peak rate information
        peak_query = session.query(PeakRate).filter(PeakRate.submission_id == entry.submission_id)

        # if it doesnt exist at all, add it
        # posting_date = datetime.fromtimestamp(entry.created)
        if peak_query.count() < 1:
            session.add(PeakRate(submission_id=entry.submission_id, rate=rate_entry.rate,
                                 time_since_creation=datetime.now(timezone.utc) - entry.created))
        # otherwise compare it to the one that exists
        else:
            old_peak = peak_query[0]
            if old_peak.rate < rate_entry.rate:
                old_peak.rate = rate_entry.rate
                old_peak.time_since_creation = datetime.now(timezone.utc) - entry.created

        print("-----------------------")

    session.commit()

    # delete expired information for Rates
    for rate in session.query(Rate).all():
        # since everything new should have an updated timestamp i think i can just
        # compare times and delete
        if (datetime.now(timezone.utc) - rate.timestamp).total_seconds() > 15:
            session.query(Rate).filter(Rate.submission_id == rate.submission_id).delete()
            print(rate.submission_id + " deleted from Rates")

    session.commit()

    # sleep
    duration = time.time() - start
    print("--- %s seconds ---" % (time.time() - start))
    time.sleep((10 * 60) - duration)