# Renta GPT

RentaGPT is a search engine inspired by [perplexity.ai](https://www.perplexity.ai/) and focused in provide answers
related to the Spanish Taxes (Renta 2022).

If you have any questions, feel free to reach out to me on [Twitter](https://twitter.com/mpuig).

[Blog Post](https://medium.com/@mpuig/developing-rentagpt-a-search-bot-for-taxes-using-langchain-chroma-and-openai-gpt-c9c56c508a62)

## How it works

RentaGPT has a vector database that stores information about the context.
The information has been crawled from the AEAT site, cleaned up, and stored as vector embeddings to make it
possible to run semantic searches through it.

Given a query, RentaGPT fetches relevant information from the database, and then it prompts OpenAI GPT-3 API to generate
an answer from the more relevant documents found in the initial step.

## How to deploy to fly.io

Create an account to [fly.io](https://fly.io)

First configure the app:

```
fly launch
```

Deploy the app to your account:

```
flyctl deploy --remote-only
```

Setup some server parameters to make it work properly:

```
flyctl ips allocate-v4
flyctl scale memory 1024
```

Set secrets.

```
fly secrets set API__PORT=8080
fly secrets set API__HOST=0.0.0.0
fly secrets set CHROMA__COLLECTION_NAME="renta22"
fly secrets set PROVIDERS__OPENAI__API_KEY="sk-YOUR_OPENAI_API_KEY"
```

Note about secrets: the `openai_api_key` is only used during the ingestion process

## Requirements

Get OpenAI API key [here](https://openai.com/api/).

## Credits

Shoutout to [Clarity AI](https://github.com/mckaywrigley/clarity-ai) for the frontend inspiration.
