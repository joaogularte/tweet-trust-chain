import math
import requests
import os

def twitter_api(route, params):
  """Utilitarian fuction to send Http requests to Twitter API

  Parameters:
    route (string): route of Twitter endpoint
    params (dict): query params of Twitter endpoint

  Result:
    dict: Twitter endpoint response on json
  """

  host = "https://api.twitter.com"
  url = host + route
  token = os.getenv('TWITTER_API_TOKEN')
  headers = {'Authorization': 'Bearer ' + token}

  response = requests.get(url, headers=headers, params=params)

  return response.json()

def get_tweet_collection(hashtag, max_results = 10):
  """Get a collections of tweets based on retweets about a specfic hashtag

  Parameters:
    hashtag (string): hashtag related with tweets
    max_results (int): the maximum number of result to be returned

  Result:
    list: collection of items which have the following struct:

        {
          'id': (string),
          'author_id': (string),
          'text': (string),
          'referenced_tweets': [
            {
              'type': (string ),
              'id': (string),
              'author_id': (string)
            }
          ]
        }

  """

  query = hashtag + ' is:quote is:retweet'
  expansions = 'referenced_tweets.id.author_id'
  max_results = max_results
  tweet_fields = 'referenced_tweets'

  params = {'query': query, 'expansions':expansions, 'max_results': max_results, 'tweet.fields': tweet_fields}

  response = twitter_api('/2/tweets/search/recent', params)
  return parse_tweet_collection(response)

def get_user_info(id):
  """Get information about user profile

  Parameters:
    id (string): user identification

  Result:
    dict: dictonary with user information:

        {
          'id': (string),
          'followers': (string),
          'tweets': (string)
        }

  """

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

def bm25f(retweet_id, collection):
  print("Computing Bm25f value...\n")
  w = weight(retweet_id, collection)
  print(f"Weight value: {w}\n")
  idf = inverse_document_function(retweet_id, collection)
  print(f"Inverse document value: {idf}\n")
  k1 = 1.5

  print(f"Bm25f formula: ({w}/({k1} + {w})) x {idf}\n\n")

  return (w/(k1 + w)) * idf

def weight(retweet_id, collection):
  print("Computing Weight factor...\n")
  occurs = sum(map(lambda item: item['referenced_tweets'][0]['id'] == retweet_id, collection))
  boost = 3.55
  author_id = next(tweet['referenced_tweets'][0]['author_id'] for tweet in collection if tweet['referenced_tweets'][0]['id'] == retweet_id)
  b = 0.6
  user_info = get_user_info(author_id)
  user_tweets = user_info['tweets']
  user_followers = user_info['followers']
  print(
    f"Weight factor variables:\n" +
    f"Occurs: {occurs}\n" +
    f"Boost: {boost}\n"+
    f"User Tweets: {user_tweets}\n" +
    f"User Followers: {user_followers}\n" +
    f"B: {b}\n\n"+
    f"Weight formula: ({occurs} X {boost})/((1 - {b}) + {b} x ({user_tweets}/{user_followers}))\n\n"
  )
  return (occurs * boost)/((1 - b) + b * (user_tweets/user_followers))

def inverse_document_function(retweet_id, collection):
  print("Computing Inverse document function factor...\n")

  number_of_tweets = len(collection)
  number_of_tweets_related_with_retweet_id = sum(map(lambda item: item['referenced_tweets'][0]['id'] == retweet_id, collection))

  print(
    f"Tweet number inside collection: {number_of_tweets}\n"
    f"Tweet number linked with retweet inside collection: {number_of_tweets_related_with_retweet_id}\n\n"
    f"Inserve document function formula: log ({number_of_tweets} + {number_of_tweets_related_with_retweet_id} + 0.5) / ({number_of_tweets_related_with_retweet_id} + 0.5)\n\n"
  )

  return math.log((number_of_tweets + number_of_tweets_related_with_retweet_id + 0.5) / (number_of_tweets_related_with_retweet_id + 0.5))

def evaluate_credibility(collection):
  print('Evaluating credibility collection...\n')

  results = []

  for item in collection:
    referenced_tweet_id = item['referenced_tweets'][0]['id']
    referenced_tweet_author_id = item['referenced_tweets'][0]['author_id']

    print(
    f"Evaluating credibility of tweet id: {item['id']}\n"+
    f"Tweet text: {item['text']}\n"+
    f"Retweet id: {referenced_tweet_id}\n" +
    f"Retweet author id: {referenced_tweet_author_id}\n"
    )

    result = bm25f(referenced_tweet_id, collection)

    print(f"Bm25f value: {result}\n")

    print('--------------------------------------\n')

    results.append({'tweet_data': item, 'bm25f_result': result})

  return results

def check_credibility(evaluate_results):
  print('Checking credibility collection...\n')

  average = sum(map(lambda result: result['bm25f_result'], evaluate_results)) / len(evaluate_results)

  print(f"Bm25f collection average: {average}\n")

  has_credibility = []
  not_has_credibility = []

  for result in evaluate_results:
    if result['bm25f_result'] >= average:
      print(f"Tweet id {result['tweet_data']['id']} has credibility")
      has_credibility.append(result)
    else:
      print(f"Tweet id {result['tweet_data']['id']} not has credibility")
      not_has_credibility.append(result)

  print(
    f"Final checking result: \n\n" +
    f"Tweets have credibility: {has_credibility}\n\n" +
    f"Tweets not have credibility: {not_has_credibility}\n\n"
    )

def main():

  hashtag = '#crazy'
  max_results = 100

  collection = get_tweet_collection(hashtag, max_results)
  evaluate_result = evaluate_credibility(collection)
  check_credibility(evaluate_result)

main()
