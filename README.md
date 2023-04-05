# Renta GPT

RentaGPT is a search engine inspired by [perplexity.ai](https://www.perplexity.ai/) and focused in provide answers
related to the Spanish Taxes (Renta 2022).

If you have any questions, feel free to reach out to me on [Twitter](https://twitter.com/mpuig).

## How it works

RentaGPT has a vector database that stores information about the context.
The information has been crawled from the AEAT site, cleaned up, and stored as vector embeddings to make it
possible to run semantic searches through it.

Given a query, RentaGPT fetches relevant information from the database, and then it prompts OpenAI GPT-3 API to generate
an answer from the more relevant documents found in the initial step.

## Requirements

Get OpenAI API key [here](https://openai.com/api/).

## Credits

Shoutout to [Clarity AI](https://github.com/mckaywrigley/clarity-ai) for the frontend inspiration.
