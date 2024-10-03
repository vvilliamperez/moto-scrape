import json
import os
import re

import discord
from discord import client


from utils import *

AF1_URL = "https://www.af1racingaustin.com/search/inventory/availability/In%20Stock/usage/Used"
BUCKET = "moto-scraper"
topic_arn = 'arn:aws:sns:us-east-1:986354456027:af1-used-site-updated'
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

def check_for_updates():
    last_known_hash = get_latest_hash_in_s3(AF1_URL, BUCKET)
    current_hash = get_site_hash_now(AF1_URL)

    if not last_known_hash:
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash)
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)
        return {
            'statusCode': 200,
            'body': json.dumps('No previous hash found, storing current hash!')
        }

    if current_hash == last_known_hash:
        return {
            'statusCode': 200,
            'body': json.dumps('No updates to the site. MD5 looks the same!')
        }

    if current_hash != last_known_hash:
        # store current
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash)
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)

        # send sns
        send_sns(topic_arn)

        return {
            'statusCode': 200,
            'body': json.dumps('New site update, sent SNS to !')
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps('Unknown error occurred!')
        }


def extract_search_results_from_file_path(file_path):
    """
    Extracts all search results from a given HTML file within the 'search-results-list' div.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

        # Find the search results list container
        search_results_list = soup.find('div', class_='search-results-list')

        if not search_results_list:
            return []

        # Find all search result panels within the search results list
        search_result_panels = search_results_list.find_all('div', class_='panel panel-default search-result')

        # Extract the text content or relevant data from each search result panel
        return [panel.get_text(strip=True) for panel in search_result_panels]


def extract_search_results(text):
    """
    Extracts all search results from a given HTML file within the 'search-results-list' div.
    """
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')

    # Find the search results list container
    search_results_list = soup.find('div', class_='search-results-list')

    if not search_results_list:
        return []

    # Find all search result panels within the search results list
    search_result_panels = search_results_list.find_all('div', class_='panel panel-default search-result')

    # Extract the text content or relevant data from each search result panel
    return [panel.get_text(strip=True) for panel in search_result_panels]


def compare_search_results(old_results, new_results):
    """
    Compares two lists of search results and returns a dict with removed, updated, and added results.
    """
    old_set = set(old_results)
    new_set = set(new_results)

    removed = list(old_set - new_set)
    added = list(new_set - old_set)

    # Updated results (if necessary) would require a deeper comparison of individual items
    # Here, we're treating "updated" as something that exists in both, but its content differs.
    # Since we use strings, there might not be a perfect way to detect updates without custom logic.
    updated = [new_result for new_result in new_set if new_result in old_set and old_results != new_results]

    return {
        'removed': removed,
        'added': added,
        'updated': updated
    }


def scan_html_files_for_differences(file1, file2):
    """
    Scans two HTML files and returns a dict with the differences in the search results list.
    """
    # Extract search results from both HTML files
    old_results = extract_search_results(file1)
    new_results = extract_search_results(file2)

    # Compare the results
    differences = compare_search_results(old_results, new_results)

    return differences


#output = scan_html_files_for_differences('test/base.html', 'test/1missing.html')
#print(output)


def format_discord_message(item_data):
    if item_data is None:
        return "No valid item data to format."

    # Extract relevant fields
    name = item_data.get('item', 'Unknown')
    price = item_data.get('bestPrice', 'Price not available')
    url = item_data.get('itemUrl', '')

    # If URL is missing the "https:" prefix, add it
    if not url.startswith('http'):
        url = "https:" + url

    # Format the message for Discord
    formatted_message = f"**{name}**\nPrice: {price}\n[View More]({url})"
    return formatted_message


def extract_json_from_string(data_str):
    # Step 1: Use regex to extract JSON portion (anything between the first '{' and last '}')
    json_match = re.search(r'(\{.*\})', data_str)
    if json_match:
        json_str = json_match.group(1)  # Get the matched JSON string
        try:
            # Step 2: Parse the JSON string into a dictionary
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("Failed to decode JSON")
            return None
    else:
        print("No JSON found in the input string.")
        return None


def send_discord_message(message):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')

        # Get the channel by ID
        for guild in client.guilds:
            print(f'Guild: {guild.name}')
            for channel in guild.text_channels:
                print(f'Channel: {channel.name} (ID: {channel.id})')
                if channel.name == 'bots':
                    if message['removed']:
                        for item in message['removed']:
                            item = extract_json_from_string(item)
                            await channel.send(f'Removed: {format_discord_message(item)}')
                    if message['added']:
                        for item in message['added']:
                            item = extract_json_from_string(item)
                            await channel.send(f'Added: {format_discord_message(item)}')

        await client.close()



    client.run(DISCORD_TOKEN)




def scrape_and_send_message():
    print(" TODO: scrape and send email")

    obj1, obj2 = get_latest_2_object_from_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"))

    html1 = get_html_from_s3(BUCKET, obj1['Key'])
    html2 = get_html_from_s3(BUCKET, obj2['Key'])

    res1 = extract_search_results(html1)
    res2 = extract_search_results(html2)

    diff = compare_search_results(res1, res2)

    print(diff)

    send_discord_message(diff)


def is_site_updated(event):
    try:
        sns_message = event['Records'][0]['Sns']['Message']
        print(f"Received SNS message: {sns_message}")
        return sns_message is not None
    except KeyError:
        return False


def lambda_handler(event, context):
    if is_site_updated(event):
        # scrape and send email
        resp = scrape_and_send_message()
    else:
        resp = check_for_updates()
    return resp

# get_latest_hash_in_s3(AF1_URL, BUCKET)

# print(current_hash)


#send_discord_message(output)
