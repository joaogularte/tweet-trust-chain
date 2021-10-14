import math
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
  return parse_tweet_collection(response)

def get_user_info(id):
  url = '/2/users/' + id
  params = {'user.fields': 'public_metrics'}

  response = twitter_api(url, params)
  return parse_user_info(response)

def parse_tweet_collection(response):
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

def parse_user_info(response):
  return {'id': response['data']['id'], 'followers': response['data']['public_metrics']['followers_count'], 'tweets': response['data']['public_metrics']['tweet_count']}

def weight(retweet_id, collection):
  occurs = sum(map(lambda item: item['referenced_tweets'][0]['id'] == retweet_id, collection))
  boost = 3.55
  author_id = next(tweet['referenced_tweets'][0]['author_id'] for tweet in collection if tweet['referenced_tweets'][0]['id'] == retweet_id)
  b = 0.6
  user_info = get_user_info(author_id)
  user_tweets = user_info['tweets']
  user_followers = user_info['followers']

  return (occurs * boost)/((1 - b) + b x (user_tweets/user_followers))

def inverse_document_function(retweet_id, collection):
  number_of_tweets = len(collection)
  number_of_tweets_related_with_retweet_id = sum(map(lambda item: item['referenced_tweets'][0]['id'] == retweet_id, collection))

  return math.log((number_of_tweets + number_of_tweets_related_with_retweet_id + 0.5) / (number_of_tweets_related_with_retweet_id + 0.5))

def bm25f(retweet_id, collection):

  weight = weight(retweet_id, collection)
  print(f'Weight value: {weight}')
  idf = inverse_document_function(retweet_id, collection)
  print(f'Inverse document value: {idf}')
  k1 = 1.5

  return (weight/(k1 + weight)) * idf

def evaluate_credibility(collection):
  print('Evaluating credibility collection...')

  results = []

  for item in collection:
    referenced_tweet_id = item['referenced_tweets'][0]['id']
    referenced_tweet_author_id = item['referenced_tweets'][0]['author_id']

    print(
    f'Evaluating credibility of tweet id: {item['id']}\n'+
    'Tweet text: {item['text']}\n'+
    'Retweet id: {referenced_tweet_id}' +
    'Retweet author id: {referenced_tweet_author_id}\n' +
    )

    result = bm25f(referenced_tweet_id, collection)

    print(f'Bm25f value: {result}')

    results.append({'tweet_data': item, 'bm25f_result': result})

  return results

def check_credibility(evaluate_results):
  average = sum(map(lambda result: result['bm25f_result'], evaluate_results)) / len(evaluate_results)




def main():
  collection = get_tweet_collection('#crazy')
  some_id = collection[0]['referenced_tweets'][0]['author_id']
  print(get_user_info(some_id))

main()
