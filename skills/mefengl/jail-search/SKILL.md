---
name: jail-search
description: Search a billion+ documents — papers, books, code, legal cases, forums, Wikipedia, and more.
metadata: {"openclaw":{"requires":{"bins":["curl"]},"optionalEnv":["JAIL_API_KEY"],"emoji":"🔍","homepage":"https://jail.li"},"hermes":{"tags":["search","research","knowledge"],"category":"research"}}
---

# JAIL Search

Search documents. Returns ranked results with title, author, year, description, url, id, score — not full content. Use URLs from results with fetch/browsing to read actual documents.

Use when: user asks to research, find papers/books/articles, look up facts, find discussions, legal cases, or any "search for..." request.

Strategy: use 2-4 keywords per query (English preferred). Pick the right type first. Try synonyms if few results. Search across multiple types to cross-reference. Use detail() for full metadata on promising results.

## Types

| Type | Content |
|------|---------|
| `academic` | OpenAlex/arXiv/Semantic Scholar/DBLP |
| `wiki` | Wikipedia 18 languages |
| `books` | books/digital libraries |
| `legal` | Case Law/CourtListener/EUR-Lex |
| `forums` | HN/StackExchange/Lobsters/LessWrong/60+ |
| `economics` | World Bank/IMF/FRED |
| `packages` | npm/PyPI/Crates.io |
| `knowledge` | Wikidata |
| `news` | news articles |
| `music` | Discogs/MusicBrainz |
| `video` | IMDb/YouTube |
| `health` | clinical trials |
| `geo` | world places |
| `fandom` | fan wikis |
| `tech` | Dev.to |
| `audio` | podcasts |
| `social` | Reddit/Mastodon/Lemmy |
| `crypto` | DeFi/tokens |
| `predictions` | prediction markets |

## Search

```bash
curl -Gs "https://api.jail.li/v1/search" --data-urlencode "q=QUERY" -d "type=TYPE&limit=10"
```

Paginate: add `&cursor=CURSOR` using `next_cursor` from previous response.

## Detail

```bash
curl -s "https://api.jail.li/v1/detail/DOC_ID"
```

With API key: add `-H "Authorization: Bearer $JAIL_API_KEY"`
