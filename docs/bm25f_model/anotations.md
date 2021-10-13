Modelo para o algoritmo que implementa o BM25F:

- buscar os tweets dos ultimos setes dias baseados em uma hashtag
- Para cada tweet da coleção, analisar a fonte do tweet (referenced tweet) com o bm25f:
- Tirar a média e comparar cada um isoladamente.

Anotações API Twitter:

GET /2/tweets/search/recent - Rota para retornar os tweets dos últimos setes dias baseados na query informada.

Endpoint URL

https://api.twitter.com/2/tweets/search/recent


Query = #hashtag is:quote is:retweet
expansions = referenced_tweets.id.author_id
max_results = 100
next_token = token of the next page
start_time = YYYY-MM-DDTHH:mm:ssZ
tweet.fields = referenced_tweets

URL = Id do retweet

GET /2/users/:id - Rota para retornar os dados do usuario ou autor do tweet

id: 1329070861144395777
user.fields = public_metrics
