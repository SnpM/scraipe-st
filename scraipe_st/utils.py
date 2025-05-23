from abc import ABC, abstractmethod
from typing import final, Tuple, Dict, Any, Type, Protocol
from scraipe.classes import IScraper, IAnalyzer
from collections import OrderedDict
from pydantic import BaseModel
import requests
import aiohttp
import asyncio
from scraipe.async_util.async_manager import AsyncManager
import random
import numpy as np
import logging

import scraipe.extended

def label2anchor(label:str) -> str:
    """
    Convert a label to an anchor.
    
    Args:
        label (str): The label to convert.
        
    Returns:
        str: The anchor string.
    """
    return label.replace(" ", "-").lower()

async def _get_random_wikipedia_links(n=10):
    base_url = "https://en.wikipedia.org"
    MAX_WORKERS = 4
    async with aiohttp.ClientSession() as session:
        sem = asyncio.Semaphore(MAX_WORKERS)
        async def fetch_random_link():
            async with sem:
                async with session.head("https://en.wikipedia.org/wiki/Special:Random", allow_redirects=False) as response:
                    link = response.headers.get("Location")
                    if link and link.startswith("/"):
                        link = base_url + link
                    return link
        tasks = [fetch_random_link() for _ in range(n)]
        results = await asyncio.gather(*tasks)
    return [r for r in results if r]

def get_random_wikipedia_links(n=10):
    """
    Get n random Wikipedia links.
    
    Args:
        n (int): The number of random links to get.
        
    Returns:
        list: A list of random Wikipedia links.
    """
    return AsyncManager.get_executor().run(_get_random_wikipedia_links(n))

tme_messageid_space =  np.arange(1, 1000)
tme_channel_space = [
    "https://t.me/binancesignals",
    "https://t.me/carnegiemellonuniversity",
    "https://t.me/telegram",
    "https://t.me/TheHackerNews",
]
def get_tme_links(n=10):
    """
    Get n random Telegram links.
    
    Args:
        n (int): The number of random links to get.
        
    Returns:
        list: A list of random Telegram links.
    """
    channels = np.random.choice(tme_channel_space, size=n, replace=True)
    message_ids = np.random.choice(tme_messageid_space, size=n, replace=False)
    links = [f"{c}/{m}" for c, m in zip(channels, message_ids)]
    return links


from scraipe.extended import RedditLinkCollector
import CONFIG
import asyncpraw

subreddits = [
    "bjj",
    "osint",
    "opensource",
    "python",
    "colorado",
    "programming",
    "datascience"
]
def get_reddit_links(n=10):
    """
    Get n random Reddit links.
    
    Args:
        n (int): The number of random links to get.
        
    Returns:
        list: A list of random Reddit links.
    """
    if not CONFIG.REDDIT_CLIENT_ID or not CONFIG.REDDIT_CLIENT_SECRET:
        logging.error("Reddit client ID and secret must be configured in environment variables.")
        return []
    
    async def _get_reddit_links(n=10):
        """
        Get n random Reddit links.
        
        Args:
            n (int): The number of random links to get.
            
        Returns:
            list: A list of random Reddit links.
        """
        client = asyncpraw.Reddit(
            client_id=CONFIG.REDDIT_CLIENT_ID,
            client_secret=CONFIG.REDDIT_CLIENT_SECRET,
            user_agent="scraipe_st random gen (u/petertigerr)",)
        
        
        links = []
        async with client:
            subreddit = random.choice(subreddits)
            subreddit = await client.subreddit(subreddit)
            
            async for submission in subreddit.top(limit=n * 5):
                link = "https://reddit.com" + submission.permalink
                links.append(link)
        return random.sample(links, n)
    return AsyncManager.get_executor().run(_get_reddit_links(n))
            
    