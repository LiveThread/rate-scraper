import time
import json

from scraper.models import Rate

# TODO: logging from a seperate process doesnt reach main console output
def export_json(logger, db_session, reddit):
    """
    Export the top 15 rates as a json file.
    :param logger: the logger being used
    :param db_session: the dbsession to query
    :param reddit: the authenticated praw instance in use
    """
    logger.debug("Starting JSON export...")
    export_start = time.time()

    # seems like PRAW is ok to operate on multiple processes without additional work.
    # http://praw.readthedocs.io/en/latest/getting_started/multiple_instances.html
    hot_post_rates = db_session.query(Rate).order_by(Rate.rate.desc()).limit(15).all()

    # turn all of the hot_post_rates into a list of their fullname (thing_id)
    hot_post_rates_fullnames = [x.submission_id for x in hot_post_rates]

    # get a generator from praw for all of these posts
    submissions = reddit.info(hot_post_rates_fullnames)

    # combine info from reddit with my calculated rates
    hot_posts = []
    for ii, submission in enumerate(submissions):
        hot_posts.append(HotPost(submission.title, submission.subreddit_name_prefixed,
                                 hot_post_rates[ii].rate, submission.created_utc))
    # generate JSON
    json_data = json.dumps(hot_posts, cls=HotPostEncoder)

    # save JSON
    f = open("data/data.json", "w")
    f.write(json_data)
    logger.debug("JSON export finished in " + str(time.time() - export_start) + " seconds")


class HotPost:
    """
    Represents the object to be exported into the JSON file.
    """

    def __init__(self, title, subreddit, comment_rate, post_date):
        """
        Create a new HotPost
        :param title: the posting title
        :param subreddit: the subreddit name that this was posted in
        :param comment_rate: the last calculated amount of comments / minute
        :param post_date: when was this submission posted?
        """
        self.title = title
        self.subreddit = subreddit
        self.comment_rate = comment_rate
        self.post_date = post_date


class HotPostEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder for HotPost.
    """

    def default(self, obj):
        if isinstance(obj, HotPost):
            return [obj.title, obj.subreddit, obj.comment_rate, obj.post_date]
        return json.JSONEncoder.default(self, obj)
