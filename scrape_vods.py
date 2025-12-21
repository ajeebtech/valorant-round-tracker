from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import re

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use webdriver-manager to automatically handle driver installation
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_match_links(driver, page_number):
    """Scrape match links from a specific results page"""
    url = f"https://www.vlr.gg/matches/results/?page={page_number}"
    
    print(f"Scraping page {page_number}...")
    driver.get(url)
    
    # Wait for match items to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "match-item"))
        )
    except:
        print(f"No match items found on page {page_number}")
        return []
    
    # Give extra time for all content to load
    time.sleep(2)
    
    # Get page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find all match links
    match_links = []
    match_items = soup.find_all('a', class_=re.compile(r'match-item'))
    
    for match in match_items:
        href = match.get('href')
        if href and href.startswith('/'):
            # Extract match ID from href (e.g., /580237/...)
            parts = href.split('/')
            if len(parts) > 1 and parts[1].isdigit():
                match_id = parts[1]
                match_links.append({
                    'match_id': match_id,
                    'url': f"https://www.vlr.gg{href}"
                })
    
    # Remove duplicates
    seen = set()
    unique_matches = []
    for match in match_links:
        if match['match_id'] not in seen:
            seen.add(match['match_id'])
            unique_matches.append(match)
    
    print(f"Found {len(unique_matches)} matches on page {page_number}")
    return unique_matches

def scrape_vod_links(driver, match_url):
    """Scrape VOD links from a specific match page"""
    driver.get(match_url)
    
    # Wait for page to load
    time.sleep(3)
    
    # Get page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find all VOD links (YouTube links)
    vod_links = []
    
    # Method 1: Find all anchor tags with YouTube/youtu.be in href
    youtube_links = soup.find_all('a', href=re.compile(r'(youtube\.com|youtu\.be)'))
    for link in youtube_links:
        href = link.get('href')
        if href:
            # Normalize YouTube URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/') and not href.startswith('//'):
                continue  # Skip relative URLs that aren't YouTube
            
            # Skip live stream URLs
            if '/live' in href:
                continue
            
            if href not in vod_links:
                vod_links.append(href)
    
    # Method 2: Look for YouTube embeds or iframes
    iframes = soup.find_all('iframe', src=re.compile(r'youtube\.com'))
    for iframe in iframes:
        src = iframe.get('src')
        if src:
            if src.startswith('//'):
                src = 'https:' + src
            if src not in vod_links:
                vod_links.append(src)
    
    # Method 3: Check for data attributes or JavaScript that might contain YouTube links
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            youtube_urls = re.findall(r'(?:https?:)?//(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\'"]+', script.string)
            for url in youtube_urls:
                if url.startswith('//'):
                    url = 'https:' + url
                if url not in vod_links:
                    vod_links.append(url)
    
    return vod_links

def main():
    """Main function to scrape all matches and VODs from pages 3 to 1"""
    driver = setup_driver()
    all_matches_data = []
    
    try:
        # Scrape pages 3, 2, 1 (in that order)
        for page in [3,2,1]:
            match_links = scrape_match_links(driver, page)
            
            for match_info in match_links:
                match_id = match_info['match_id']
                match_url = match_info['url']
                
                print(f"Scraping VODs for match {match_id}...")
                vod_links = scrape_vod_links(driver, match_url)
                
                match_data = {
                    'match_id': match_id,
                    'match_url': match_url,
                    'vod_links': vod_links,
                    'vod_count': len(vod_links)
                }
                
                all_matches_data.append(match_data)
                print(f"  Found {len(vod_links)} VOD(s) for match {match_id}")
                
                # Be respectful to the server - add a small delay
                time.sleep(1)
        
        # Save to JSON file
        output_file = 'vlr_vods.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_matches_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Scraping completed!")
        print(f"✓ Total matches scraped: {len(all_matches_data)}")
        print(f"✓ Data saved to: {output_file}")
        
        # Print summary statistics
        matches_with_vods = sum(1 for m in all_matches_data if m['vod_count'] > 0)
        total_vods = sum(m['vod_count'] for m in all_matches_data)
        print(f"✓ Matches with VODs: {matches_with_vods}/{len(all_matches_data)}")
        print(f"✓ Total VODs found: {total_vods}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
