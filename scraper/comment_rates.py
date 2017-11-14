import sys
import os.path

# appends the current "full path name of the executing script in a multiplatform-safe way"
# https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import praw
from scraper.models import Tracker, Rate, PeakRate, Base

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from datetime import datetime, timezone, timedelta
import time

from scraper import config

import logging

#    _____       _ _   _       _ _          _   _
#   |_   _|     (_) | (_)     | (_)        | | (_)
#     | |  _ __  _| |_ _  __ _| |_ ______ _| |_ _  ___  _ __
#     | | | '_ \| | __| |/ _` | | |_  / _` | __| |/ _ \| '_ \
#    _| |_| | | | | |_| | (_| | | |/ / (_| | |_| | (_) | | | |
#   |_____|_| |_|_|\__|_|\__,_|_|_/___\__,_|\__|_|\___/|_| |_|

logger = logging.getLogger("comment_rates_logger")
logger.setLevel(config.debug_level)

# create console handler and set level
# not needed unless logs go to file
# ch = logging.StreamHandler()
# ch.setLevel(config.debug_level)
#
# formatter = logging.Formatter("%(asctime)s; %(levelname)s; %(message)s",
#                                           "%Y-%m-%d %H:%M:%S")
# ch.setFormatter(formatter)
# logger.addHandler(ch)
logger.debug("Logger initialized.")

db = create_engine(config.db_connection)
logger.debug("Database engine created.")

# creates tables if they don't exist. Does not drop if they do exist.
Base.metadata.create_all(db)
logger.debug("Tables created / loaded.")

reddit = praw.Reddit(client_id=config.reddit_client_id,
                     client_secret=None,
                     user_agent='hot comment thread calculator',
                     implicit=True)
logger.debug("PRAW client connected.")

DBSession = sessionmaker(bind=db)
session = DBSession()
logger.debug("Database session initialized.")

logger.info("Started successfully...")


#    ______                _   _
#   |  ____|              | | (_)
#   | |__ _   _ _ __   ___| |_ _  ___  _ __  ___
#   |  __| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#   | |  | |_| | | | | (__| |_| | (_) | | | \__ \
#   |_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#

def get_subreddits():
    """
    Read in the lines from subreddits.txt
    :return: the list of subreddits to traverse
    """
    f = open("subreddits.txt", "r")
    subreddits = []
    for line in f:
        if line.startswith('#'):
            continue
        if line == '\n':
            continue
        subreddits.append(line.rstrip('\n'))
    return subreddits


def fetch_hot_posts(subreddits):
    """
    Fetch the top hot posts from each subreddit
    :param subreddits: the list of subrreddit names to hit
    :return: the list of those submissions
    """
    posts = []
    for sub_name in subreddits:
        logging.debug('Fetching {}'.format(sub_name))
        posts.extend(reddit.subreddit(sub_name).hot(limit=config.post_per_subreddit))
    return posts


def get_current_rates(posts):
    """
    Generate a models.Tracker in the database for each post with its current comment count and timestamp.
    :param posts: the list of PRAW posts to get the rates of
    :return: the new rates as a list of models.Tracker
    """
    new_entries = []
    for post in posts:
        # if post older than 36 hours ignore it
        post_timestamp = datetime.fromtimestamp(post.created_utc, timezone.utc)
        current_timestamp = datetime.now(timezone.utc)

        if (current_timestamp - post_timestamp) > timedelta(hours=36):
            continue

        logger.debug('Processing "{}" with title "{}"'.format(post.fullname, post.title))
        entry = Tracker(submission_id=post.fullname, comment_count=post.comments.__len__(),
                        timestamp=current_timestamp)
        entry.created = post_timestamp
        new_entries.append(entry)
    session.commit()

    return new_entries


def compare_to_previous(trackers):
    """
    Go through all of the given models.Tracker (likely all the new ones that were just made) and compare
    them to the last models.Tracker in the database to compare it and calculate a comments / minute rate
    :param trackers: a list of models.Tracker that was just fetched from reddit.
    :return:
    """
    for tracker in trackers:
        last_entry = session.query(Tracker).filter(Tracker.submission_id == tracker.submission_id)
        if last_entry.count() != 1:
            logger.debug("{} does not yet exist in Tracker table. Adding now.".format(tracker.submission_id))
            logger.debug("--------------------------------")
            session.add(tracker)
            continue
        old = last_entry[0]
        new = tracker
        # amount of new top level comments
        comment_diff = new.comment_count - old.comment_count
        # the time difference in minutes
        time_diff = (new.timestamp - old.timestamp).total_seconds() / 60

        # if there are no new comments (or if comments were deleted) then there is nothing to do.
        if comment_diff < 0:
            logger.debug("No new comments.")
            logger.debug("--------------------------------")
            continue

        logger.debug("Time since last update: {}".format(time_diff))
        logger.debug("Old total comment count: {}".format(old.comment_count))
        logger.debug("New total comment count: {}".format(new.comment_count))
        logger.debug("Difference: {}".format(comment_diff))

        # update the old Tracker in the database with the updated information
        old.comment_count = new.comment_count
        old.timestamp = new.timestamp

        # get the models.Rate for this post
        rate_entries = session.query(Rate).filter(Rate.submission_id == tracker.submission_id)

        # if this post has a previous rate, update it to the current Rate
        if rate_entries.count() > 0:
            rate_entry = rate_entries[0]
            rate_entry.rate = comment_diff / time_diff
            rate_entry.timestamp = datetime.now(timezone.utc)
        # otherwise create a new Rate
        else:
            rate_entry = Rate(submission_id=tracker.submission_id, rate=comment_diff / time_diff,
                              timestamp=datetime.now(timezone.utc))
            session.add(rate_entry)

        # peak rate information
        peak_query = session.query(PeakRate).filter(PeakRate.submission_id == tracker.submission_id)

        # if it doesnt exist at all, add it
        if peak_query.count() < 1:
            session.add(PeakRate(submission_id=tracker.submission_id, rate=rate_entry.rate,
                                 time_since_creation=datetime.now(timezone.utc) - tracker.created))
        # otherwise compare it to the one that exists
        else:
            old_peak = peak_query[0]
            if old_peak.rate < rate_entry.rate:
                old_peak.rate = rate_entry.rate
                old_peak.time_since_creation = datetime.now(timezone.utc) - tracker.created

            logger.debug("--------------------------------")

    session.commit()


def delete_old_rates():
    """
    Get rid of any old models.Rate from the database
    """
    for rate in session.query(Rate).all():
        # delete old rates from the database
        if (datetime.now(timezone.utc) - rate.timestamp).total_seconds() > 15:
            session.query(Rate).filter(Rate.submission_id == rate.submission_id).delete()
            logger.debug("{} deleted from Rates table.".format(rate.submission_id))
    session.commit()


#    ______                     _   _
#   |  ____|                   | | (_)
#   | |__  __  _____  ___ _   _| |_ _  ___  _ __
#   |  __| \ \/ / _ \/ __| | | | __| |/ _ \| '_ \
#   | |____ >  <  __/ (__| |_| | |_| | (_) | | | |
#   |______/_/\_\___|\___|\__,_|\__|_|\___/|_| |_|
#

# only read the file once.
subreddits = get_subreddits()

# run until dead...
# TODO: would chron be more appropriate?
# thoughts:
#   it would likely be better to manage that way.
#   if the server has a network issue the chron job would just restart on the next running of it
#   logging might be weird without going to a specific console -> file logging?
while True:
    start = time.time()
    logger.info('Starting scrapping at {}'.format(start))

    # get the posts from all the subreddits
    posts = fetch_hot_posts(subreddits)
    logger.debug("Finished fetching hot posts.")

    # get the current comment count / timestamp for each post
    new_trackers = get_current_rates(posts)
    logger.debug("Finished getting current rates.")

    # compare the current rates to the previous and update the peak rate
    compare_to_previous(new_trackers)
    logger.debug("Finished comparing new rates to previous rates.")

    # delete expired information for Rates
    delete_old_rates()
    logger.debug("Finished deleting old rates.")

    # sleep
    duration = time.time() - start
    sleep_time = (10 * 60) - duration
    logger.info('Scraping took {} seconds.'.format(time.time() - start))
    logger.info('Sleeping for {} seconds...'.format(sleep_time))
    time.sleep(sleep_time)
