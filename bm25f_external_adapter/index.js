const { Requester, Validator } = require('@chainlink/external-adapter')
const evaluateCredibilityPerRetweedId = require('./bm25f')

const customParams = {
  hashtag: ['hashtag'],
  referenced_tweet_id: ['referenced_tweet_id'],
  endpoint: false
}

const createRequest = (input, callback) => {
  const validator = new Validator(callback, input, customParams)
  const jobRunID = validator.validated.id
  const hashtag = validator.validated.data.hashtag
  const referencedTweetId =  validator.validated.data.referenced_tweet_id

  evaluateCredibilityPerRetweedId(hashtag, referencedTweetId)
    .then(response => {

      if (response.error) {
        response = {
          status: 404,
          data: response
        }
        callback(response.status, Requester.success(jobRunID, response))
      } else {
        response = {
          status: 200,
          data: {
            result: response
          }
        }
        callback(response.status, Requester.success(jobRunID, response))
      }
    })
    .catch(error => {
      callback(500, Requester.errored(jobRunID, error))
    })
}

module.exports.createRequest = createRequest
