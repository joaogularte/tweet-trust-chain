import requests
import os

def twitter_api(route, params):
  host = "https://api.twitter.com"
  url = host + route
  token = os.getenv('TWITTER_API_TOKEN')
  headers = {'Authorization': 'Bearer ' + token}

  response = requests.get(url, headers=headers, params=params)

  return response.json()

def get_tweet_collection(hashtag, max_results = 10):
  query = hashtag + ' is:quote is:retweet'
  expansions = 'referenced_tweets.id.author_id'
  max_results = max_results
  tweet_fields = 'referenced_tweets'

  params = {'query': query, 'expansions':expansions, 'max_results': max_results, 'tweet.fields': tweet_fields}

  response = twitter_api('/2/tweets/search/recent', params)
  return parse_response(response)


def parse_response(response):
  collection = []
  for v in response['data']:
    referenced_tweet_id = v['referenced_tweets'][0]['id']

    referenced_tweet = next(tweet for tweet in response['includes']['tweets'] if tweet['id'] == referenced_tweet_id)
    referenced_tweet_author_id = referenced_tweet['author_id']

    collection.append({
      'id': v['id'],
      'author_id': v['author_id'],
      'text': v['text'],
      'referenced_tweets': [
        {
          'type': v['referenced_tweets'][0]['type'],
          'id': referenced_tweet_id,
          'author_id': referenced_tweet_author_id
        }
      ]
    })
  return collection
