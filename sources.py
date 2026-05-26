# Source list for the AML/PEP monitoring scanner.
# Add additional feeds or HTML pages for Kenyan regulators, court rulings, gazettes, and other official news sources.

SOURCES = [
    {
        "name": "Google News - Kenya",
        "type": "rss",
        "url": "https://news.google.com/rss?hl=en-KE&gl=KE&ceid=KE:en",
        "query": False,
    },
    {
        "name": "Kenya Gazette",
        "type": "rss",
        "url": "https://gazettes.africa/gazettes/rss",
        "query": False,
    },
    {
        "name": "Kenya Law - Court Rulings",
        "type": "rss",
        "url": "https://kenyalaw.org/latest/rss",
        "query": False,
    },
    {
        "name": "IEBC Press Releases",
        "type": "html",
        "url": "https://www.iebc.or.ke/media-centre/press-releases",
        "query": False,
    },
    {
        "name": "Nation Africa",
        "type": "rss",
        "url": "https://nation.africa/rss",
        "query": False,
    },
    {
        "name": "Standard Media",
        "type": "rss",
        "url": "https://www.standardmedia.co.ke/feed",
        "query": False,
    },
    {
        "name": "Central Bank of Kenya News",
        "type": "rss",
        "url": "https://www.centralbank.go.ke/news/feed/",
        "query": False,
    },
    {
        "name": "Ethics & Anti-Corruption Commission News",
        "type": "rss",
        "url": "https://www.eacc.go.ke/category/news/feed/",
        "query": False,
    },
    {
        "name": "Judiciary News",
        "type": "rss",
        "url": "https://www.judiciary.go.ke/category/news/feed/",
        "query": False,
    },
    {
        "name": "Parliament of Kenya News",
        "type": "rss",
        "url": "https://www.parliament.go.ke/category/news/feed/",
        "query": False,
    },
]
