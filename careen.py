#!/usr/bin/env python3
#
# This is a python script for OSX that watches the clipboard and then sanitized
# any found URL. What is sanitization? this means stripping out unwanted query
# parameters that are normally tracking params and generally do not do much to
# convey information that the url is trying to send
#
# there is a companion apple shortcut you can install here:
# https://www.icloud.com/shortcuts/ecaa42a357014ff9aee6555862f2189e
#
# You the user will have to define the PAYWALL_SITES list You the user will
# have to define the ARCHIVE_DOMAINS
#
# The reason this is is so that *I* don't get in trouble with either the
# PAYWALL_SITES or ARCHIVE_DOMAIN operators and owners
#
# Install: pip install requests attrs pyobjc-framework-AppKit
#
# Usage: python3 ./careen.py
#
# TODO: see if anyone finds this useful other than me and if so maybe make it a
# little more userfriendly a way to achieve parity w/ an iOS shortcut would be
# great
#
# --timball@gmail.com Sat Feb 28 11:54:35 EST 2026

import time
import re
import requests
import random
from typing import List, Dict, Optional, Callable, Pattern, Union, Any
from attr import define, field
from AppKit import NSPasteboard, NSStringPboardType
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, ParseResult

# --- TYPE ALIASES ---
StrategyFunc = Callable[[ParseResult], str]


# --- STRATEGY DEFINITIONS ---
def follow_redirect(parsed: ParseResult) -> str:
    """Follows a 301/302 redirect and then cleans the resulting destination URL."""
    original_url: str = urlunparse(parsed)
    try:
        headers: Dict[str, str] = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response: requests.Response = requests.get(
            original_url,
            headers=headers,
            timeout=5,
            allow_redirects=False
        )
        if 300 <= response.status_code < 400 and 'Location' in response.headers:
            redirect_url: str = response.headers['Location']
            return clean_url(redirect_url)

    except Exception as e:
        print(f"❌ Failed to resolve Google search.app link: {e}")

    return original_url

def keep_all(parsed: ParseResult) -> str:
    """ a strat to keep everything untouched """
    return urlunparse(parsed)

def strip_all(parsed: ParseResult) -> str:
    """The default strategy: Nuke all query params and fragments."""
    return urlunparse(parsed._replace(query='', fragment=''))

def keep_specific_params(keep_list: List[str], extra: Optional[Dict[str, str]] = None) -> StrategyFunc:
    """Returns a function that only keeps parameters in the keep_list."""
    def strategy(parsed: ParseResult) -> str:
        query_params: Dict[str, List[str]] = parse_qs(parsed.query)
        new_params: Dict[str, Union[str, List[str]]] = {
            k: v for k, v in query_params.items() if k in keep_list
        }
        if extra:
            new_params = {**new_params, **extra}

        new_query: str = urlencode(new_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query, fragment=''))
    return strategy

def amazon_strategy(parsed: ParseResult) -> str:
    """Custom logic for Amazon: Clean the path AND the query."""
    path: str = parsed.path
    if "/ref=" in path:
        path = path.split("/ref=")[0]
    return urlunparse(parsed._replace(path=path, query='', fragment=''))

def apple_news_strategy(parsed: ParseResult) -> str:
    """Fetches the Apple News wrapper page and extracts the original source URL."""
    original_url: str = urlunparse(parsed)
    try:
        headers: Dict[str, str] = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response: requests.Response = requests.get(original_url, headers=headers, timeout=5)

        match: Optional[re.Match] = re.search(r'redirectToUrlAfterTimeout\("([^"]+)"', response.text)
        if match:
            source_url: str = match.group(1)
            return clean_url(source_url)
    except Exception as e:
        print(f"❌ Failed to resolve Apple News link: {e}")

    return original_url


# --- ATTRS DATA STRUCTURE ---
@define
class Rule:
    pattern: str
    strategy: StrategyFunc
    _regex: Pattern = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._regex = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, netloc: str) -> bool:
        return bool(self._regex.search(netloc))

# --- CONFIGURATION ---

# List a domain that uses the Memento protocol
# https://mementoweb.org/guide/quick-intro/ to save a domain. the feature
# needed is that  you can query the archive domain like:
#     <ARCHIVE_DOMAIN/<FULL_URL>
# so like
# https://somearchivesite.tld/https://someurl.tld/you/wanna/see


ARCHIVE_DOMAINS: List[str] = [
    "somearchive.tld",
    "someotherarchive.tld",
]

PAYWALL_SITES: List[str] = [
    r'(^|\.)paywallsite\.com$',
    r'(^|\.)otherpaywallsite\.com$',
    r'(^|\.)yetanotherpaywallsite\.com$',
]

STRATEGIES: List[Rule] = [
    Rule(
        pattern=r'^(admin|docs|drive|sheets|slides|forms|mail|calendar|sites|meet|chat|contacts)\.google\.',
        strategy=keep_specific_params(['tab', 'gid', 'usp', 'authuser'])
    ),
    Rule(
        pattern=r'(^|\.)google\.(com|ad|ae|al|am|as|at|az|ba|be|bf|bg|bi|bj|bs|bt|by|ca|cd|cf|cg|ch|ci|cl|cm|cn|cv|cz|de|dj|dk|dm|dz|ee|es|fi|fm|fr|ga|ge|gg|gl|gm|gp|gr|hn|hr|ht|hu|ie|im|iq|is|it|je|jo|kg|ki|kz|la|li|lk|lt|lu|lv|md|me|mg|mk|ml|mn|ms|mu|mv|mw|ne|nl|no|nr|nu|pl|pn|ps|pt|ro|rs|ru|rw|sc|se|sh|si|sk|sm|sn|so|sr|st|td|tg|tk|tl|tm|tn|to|tr|tt|ua|vg|vu|ws)(\.[a-z]{2,3})?$',
        strategy=keep_specific_params(['q'], {"udm": "14", "pws": "0"})
    ),
    Rule(
        pattern=r'(^|\.)amazon\.(com|ca|com\.mx|com\.br|co\.uk|de|fr|it|es|nl|se|pl|com\.tr|ae|sa|eg|in|com\.au|co\.jp)(\.[a-z]{2,3})?$',
        strategy=amazon_strategy
    ),
    Rule(pattern=r'(^|\.)reddit\.com$', strategy=strip_all),
    Rule(pattern=r'(^|\.)youtube\.com$', strategy=keep_specific_params(['v', 't'])),
    Rule(pattern=r'^youtu\.be$', strategy=keep_specific_params(['t'])),
    Rule(pattern=r'(^|\.)twitch\.tv$', strategy=keep_specific_params(['t'])),
    Rule(pattern=r'^apple\.news$', strategy=apple_news_strategy),
    Rule(pattern=r'(^|\.)nytimes\.com$', strategy=keep_specific_params(['unlocked_article_code'])),
    Rule(pattern=r'^admin\.cloud\.microsoft$', strategy=keep_all),
    Rule(pattern=r'search\.app$', strategy=follow_redirect)
]

# --- THE ENGINE ---

def clean_url(url_string: str) -> str:
    try:
        url_string = url_string.strip()
        if not url_string.startswith(('http://', 'https://')):
            return url_string

        # Infinite loop prevention
        if any(domain in url_string for domain in ARCHIVE_DOMAINS):
            return url_string

        parsed: ParseResult = urlparse(url_string)
        netloc: str = parsed.netloc.lower()

        # 1. FIND STRATEGY
        selected_strategy: StrategyFunc = strip_all
        for rule in STRATEGIES:
            if rule.matches(netloc):
                selected_strategy = rule.strategy
                break

        # 2. APPLY STRATEGY
        cleaned_url_string: str = selected_strategy(parsed)

        # 3. PAYWALL BYPASS (Skip if keep_all was used)
        if selected_strategy == keep_all:
            return cleaned_url_string

        is_paywall: bool = any(re.search(p, netloc, re.I) for p in PAYWALL_SITES)

        if is_paywall:
            mirror: str = random.choice(ARCHIVE_DOMAINS)
            return f"https://{mirror}/{cleaned_url_string}"

        return cleaned_url_string

    except Exception as e:
        print(f"⚠️ Error cleaning URL: {e}")
        return url_string

def monitor_clipboard() -> None:
    pb: NSPasteboard = NSPasteboard.generalPasteboard()
    last_change_count: int = pb.changeCount()

    print("🚀 URL Sanitizer Active. Monitoring tracking & paywalls...")

    while True:
        current_change_count: int = pb.changeCount()
        if current_change_count != last_change_count:
            original: Optional[str] = pb.stringForType_(NSStringPboardType)

            if original and original.startswith('http'):
                cleaned: str = clean_url(original)

                if cleaned != original:
                    pb.clearContents()
                    pb.setString_forType_(cleaned, NSStringPboardType)
                    print(f"\n🔗 Original:  {original}")
                    print(f"✨ Processed: {cleaned}")

            last_change_count = current_change_count
        time.sleep(0.5)

if __name__ == "__main__":
    monitor_clipboard()
