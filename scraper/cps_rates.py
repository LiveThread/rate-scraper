# calculate the rate of (total subreddit comments / day) / (total submissions / day)
# cps = comments / submissions
import praw
from scraper import config

reddit = praw.Reddit(client_id=config.reddit_client_id,
                     client_secret=None,
                     user_agent='hot comment thread calculator',
                     implicit=True)

# can we get a lot of comments at once?
# looks like we are capped at 1000.. hmm
comments = reddit.subreddit('askreddit').comments(limit=2000)
print(len(list(comments)))