from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def extract_google_urls(html_content):
    """
    Extract googleusercontent.com URLs from HTML content.
    
    Args:
        html_content (str): The HTML content to parse
        
    Returns:
        list: List of found googleusercontent.com URLs
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements that might contain URLs
    elements = soup.find_all(['img', 'a', 'link'])
    
    # Extract URLs using regex
    urls = []
    for element in elements:
        # Check different attributes that might contain URLs
        for attr in ['src', 'href', 'data-src']:
            if element.get(attr):
                url = element[attr]
                if 'googleusercontent.com' in url:
                    urls.append(url)
    
    # Remove urls that contain https://lh3
    urls = [url for url in urls if 'https://lh3' not in url]
    
    return urls

def get_champion_urls():
    # Read the HTML file
    with open('src/data/img_url_hack.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract URLs
    urls = extract_google_urls(html_content)
    
    # Pair every two urls
    paired_urls = [urls[i:i+2] for i in range(0, len(urls), 2)]

    return paired_urls

if __name__ == '__main__':
    print(get_champion_urls())
