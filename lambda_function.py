import feedparser
import arxiv
from datetime import datetime, timedelta
import tweepy
import json
import sys
import time
sys.path.append('python_package')
# coding: UTF-8


def lambda_handler(event, context):
    bot = json.loads(event)['bot']
    config = json.load(open('config.json', 'r'))
    client = tweepy.Client(config[bot]['bearerToken'], config[bot]['consumerKey'],
                           config[bot]['consumerSecret'], config[bot]['accessToken'], config[bot]['accessTokenSecret'])
    feed_url = config[bot]['feed_url']
    name = config[bot]['name']
    full_name = config[bot]['full_name']

    results = get_daily_arxiv_papers(feed_url)
    preprints = get_detail_arxiv_papers(results)

    # make a tweet of the date
    date = date_tweet(len(preprints), name, full_name)
    client.create_tweet(text=date)

    for preprint in preprints:
        text = make_tweet(preprint)
        time.sleep(10)
        tweet_id = client.create_tweet(text=text).data['id']

        abst = preprint['abstract']
        abst = replace_newline(abst)

        number = (len(abst) - 1) // 270 + 1
        i = 1
        while len(abst) > 0:
            time.sleep(10)
            if len(abst) > 270:
                text = abst[:270] + '...[%d/%d]' % (i, number)
                tweet_id = client.create_tweet(
                    text=text, in_reply_to_tweet_id=tweet_id).data['id']
                abst = abst[270:]
                i += 1
            else:
                text = abst + ' [%d/%d]' % (i, number)
                client.create_tweet(
                    text=text, in_reply_to_tweet_id=tweet_id)
                abst = ''


def date_tweet(n, name, full_name):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    date = yesterday.strftime('%Y-%m-%d')

    result = "[%s, %d new articles found for %s %s]" % (
        date, n, name, full_name)
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
    pl = {"bot": "pl"}
    pl = json.dumps(pl)
    lambda_handler(pl, None)


if __name__ == "__main__":
    main()
