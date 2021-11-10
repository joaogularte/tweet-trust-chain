const {Requester} = require('@chainlink/external-adapter')
const { response } = require('express')

const customError = (data) => {
  if (data.Response === 'Error') return true
  return false
}

const twitterApi = async (route, params) => {
  const host = "https://api.twitter.com"
  const url = `${host}${route}`
  const token = process.env.TWITTER_API_TOKEN
  const headers = {'Authorization': `Bearer ${token}`}

  const config = {
    headers: headers,
    url: url,
    params: params
  }

  return await Requester.request(config, customError)
}

const getTweetCollection = async (hashtag) => {
  const params = {
    'query': `${hashtag} is:quote is:retweet`,
    'expansions': "referenced_tweets.id.author_id",
    'max_results': 100,
    'tweet.fields': "referenced_tweets"
  }

  const response = await twitterApi("/2/tweets/search/recent", params)
  return parseTweetCollection(response.data)
}

const parseTweetCollection = (response) => {
  collection = []

  for (const v of response.data) {
    referencedTweetId = v.referenced_tweets[0].id


    referencedTweet = response.includes.tweets.find(tweet => tweet.id == referencedTweetId)
    referencedTweetAuthorId = referencedTweet.author_id

    collection.push({
      id: v.id,
      author_id: v.author_id,
      text: v.text,
      referenced_tweets: [{
        type: v.referenced_tweets[0].type,
        id: referencedTweetId,
        author_id: referencedTweetAuthorId
      }]
    })
  }

  return collection
}

const getUserInfo = async (id) => {
  url = `/2/users/${id}`
  params = {
    'user.fields': 'public_metrics'
  }

  const response = await twitterApi(url, params)
  return parseUserInfo(response.data)
}

const parseUserInfo = (response) => {
  return {
    id: response.data.id,
    followers: response.data.public_metrics.followers_count,
    tweets: response.data.public_metrics.tweet_count,
  }
}

const bm25F = async (retweetId, collection) => {
  const w = await weight(retweetId, collection)
  const idf = inverseDocumentFunction(retweetId, collection)
  const k1  = 1.5

  return (w/(k1 + w)) * idf
}

const weight = async (retweetId, collection) => {
  const occurs = collection.filter((item) => {
    return item.referenced_tweets[0].id == retweetId ? true : false
  }).length

  const boost = 3.55
  const b = 0.6
  const item = collection.find((item) => item.referenced_tweets[0].id == retweetId)
  const authoId = item.referenced_tweets[0].author_id
  const userInfo =  await getUserInfo(authoId)

  const userTweets = userInfo.tweets
  const userFollowers = userInfo.followers


  return (occurs * boost)/((1 - b) + b * (userTweets/userFollowers))
}

const inverseDocumentFunction = (retweetId, collection) => {
  const numberOfTweets =  collection.length
  const numberOfTweetsRelatedWithRetweetId = collection.filter((item) => {
    return item.referenced_tweets[0].id == retweetId ? true : false
  }).length

  return Math.log(
    (numberOfTweets + numberOfTweetsRelatedWithRetweetId + 0.5) / (numberOfTweetsRelatedWithRetweetId + 0.5)
  )
}

const bm25fAverage = (items) => {
  let total = 0

  for (const item of items) {
    total += item["bm25f_result"]
  }
  return total/items.length
}

const evaluateCredibility = async (hashtag) => {
  let results = []
  let average = 0

  collection = await getTweetCollection(hashtag)


  for (const item of collection) {
    referencedTweetId = item['referenced_tweets'][0]['id']
    result = await bm25F(referencedTweetId, collection)

    results.push({tweet_data: item, bm25f_result: result})
  }

  average = bm25fAverage(results)


  return {bm25f_average: average, data: results}
}

const evaluateCredibilityPerRetweedId = async (hashtag, retweetId) => {
  const evaluateResult = await evaluateCredibility(hashtag)
  const result = evaluateResult.data.find(result => {
    return result['tweet_data']['referenced_tweets'][0]['id'] == retweetId
  })

  if (result) {
    return {bm25f_average: evaluateResult.bm25f_average, retweet_id_bm25f_rate: result.bm25f_result}
  } else {
    return {error: "retweed_id_not_found"}
  }
}

module.exports = evaluateCredibilityPerRetweedId
