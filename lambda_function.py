import feedparser
import arxiv
from datetime import datetime, timedelta
import tweepy
import json
import sys
import time
sys.path.append('python_package')
# coding: UTF-8

feed_url = "http://arxiv.org/rss/cs.LO"


def lambda_handler(event, context):
    config = json.load(open('config.json', 'r'))
    client = tweepy.Client(config['twitter']['bearerToken'], config['twitter']['consumerKey'],
                           config['twitter']['consumerSecret'], config['twitter']['accessToken'], config['twitter']['accessTokenSecret'])

    results = get_daily_arxiv_papers(feed_url)
    preprints = get_detail_arxiv_papers(results)

    # make a tweet of the date
    date = date_tweet(len(preprints))
    client.create_tweet(text=date)

    for preprint in preprints:
        text = make_tweet(preprint)
        time.sleep(10)
        tweet_id = client.create_tweet(text=text).data['id']

        abst = preprint['abstract']
        abst = replace_newline(abst)

        number = (len(abst) - 1) // 269 + 1
        i = 1
        while len(abst) > 0:
            time.sleep(10)
            if len(abst) > 269:
                text = abst[:269] + '...[%d/%d]' % (i, number)
                tweet_id = client.create_tweet(
                    text=text, in_reply_to_tweet_id=tweet_id).data['id']
                abst = abst[269:]
                i += 1
            else:
                text = abst + ' [%d/%d]' % (i, number)
                client.create_tweet(
                    text=text, in_reply_to_tweet_id=tweet_id)
                abst = ''


def date_tweet(n):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    date = yesterday.strftime('%Y-%m-%d')

    result = "[%s, %d new articles found for mathCT Category Theory]" % (
        date, n)
    return result


def make_tweet(preprint):
    # make a string of the contents of the tweet from data of preprint
    tweet = preprint['authors'] + '\n'
    tweet += '\"' + preprint['title'] + '\"'
    tweet += preprint['url']
    return tweet


def replace_newline(text):
    lines = text.split('\n')
    for i in range(len(lines)):
        if lines[i].startswith(' ') or lines[i] == '':
            if i > 0:
                lines[i-1] += '\n'
        elif not lines[i].endswith(' '):
            lines[i] += ' '
    return ''.join(lines)


def get_daily_arxiv_papers(feed_url):
    id_list = []
    # Fetch the RSS feed
    feed = feedparser.parse(feed_url)

    # Iterate over the entries in the feed
    for entry in feed.entries:
        id = entry.id.split(':')[-1]
        id_list.append(id)
    return id_list


def get_detail_arxiv_papers(id_list):
    results = arxiv.Search(
        id_list=id_list,
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate,  # LastUpdatedDate
        sort_order=arxiv.SortOrder.Descending
    ).results()

    # Extract relevant information from the API response
    preprints = []
    for paper in results:
        preprint = {
            'title': paper.title,
            'authors': ', '.join(map(lambda author: author.name, paper.authors)),
            'abstract': paper.summary,
            'url': paper.links[0].href
        }
        if preprint['url'].endswith('v1'):
            preprints.append(preprint)
    return preprints


def main():
    # lambda_handler(None, None)
    results = get_daily_arxiv_papers(feed_url)
    preprints = get_detail_arxiv_papers(results)
    print(json.dumps(preprints, indent=2))


if __name__ == "__main__":
    main()
