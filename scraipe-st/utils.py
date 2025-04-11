from abc import ABC, abstractmethod
from typing import final, Tuple, Dict, Any, Type, Protocol
from scraipe.classes import IScraper, IAnalyzer
from collections import OrderedDict
from pydantic import BaseModel
import requests

def label2anchor(label:str) -> str:
    """
    Convert a label to an anchor.
    
    Args:
        label (str): The label to convert.
        
    Returns:
        str: The anchor string.
    """
    return label.replace(" ", "-").lower()

def get_random_wikipedia_links(n=10):
    random_links = []
    base_url = "https://en.wikipedia.org"
    for i in range(n):
        # Disable redirects so that the random link is in the "Location" header.
        response = requests.get("https://en.wikipedia.org/wiki/Special:Random", allow_redirects=False)
        # Extract the random link from the "Location" header.
        if 'Location' in response.headers:
            link = response.headers['Location']
            # If the link is relative, prepend the base URL.
            if link.startswith('/'):
                link = base_url + link
            random_links.append(link)
    return random_links