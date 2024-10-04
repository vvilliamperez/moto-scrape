import json
import re
from datetime import datetime
import requests
import boto3
import urllib.parse

from botocore.exceptions import ClientError
from bs4 import BeautifulSoup

s3_client = boto3.client('s3')


def url_to_s3_path(url, prefix=None):
    # Step 1: Parse the URL
    parsed_url = urllib.parse.urlparse(url)

    # Step 2: Combine the netloc (domain) and path (URL path) into a path-like structure
    # Remove the leading slash in the path for cleaner structure
    domain = parsed_url.netloc
    path = parsed_url.path.lstrip('/')

    # Step 3: Decode URL-encoded characters (like %20) into spaces or other meaningful characters
    decoded_path = urllib.parse.unquote(path)

    # Step 4: Replace slashes (/) with underscores (_) or another separator to create a clean S3 key
    s3_friendly_path = domain + '/' + decoded_path.replace('/', '_')

    # Step 5: Optionally add query parameters to the path structure (if any)
    if parsed_url.query:
        query = urllib.parse.unquote(parsed_url.query)
        query_part = query.replace('&', '_').replace('=', '-')
        s3_friendly_path += f'_{query_part}'

    # Step 6: Optionally add a prefix to the S3 key
    if prefix:
        s3_friendly_path = f'{prefix}/{s3_friendly_path}'

    return s3_friendly_path


def send_sns(topic_arn):
    sns_client = boto3.client('sns')

    response = sns_client.publish(
        TopicArn=topic_arn,
        Message='New site update detected!',
        Subject='Site Update'
    )

    print(f"Sent SNS message with message ID: {response['MessageId']}")


def get_latest_object_from_s3(bucket_name, subdirectory):
    """
    Retrieve the latest object from a specific subdirectory in the S3 bucket based on the LastModified date.
    """
    try:
        # List all objects in the subdirectory (using Prefix to simulate a subdirectory)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=subdirectory)

        # Check if the subdirectory is empty
        if 'Contents' not in response:
            print(f"No objects found in the subdirectory: {subdirectory}")
            return None

        # Sort objects by the LastModified date to get the latest one
        sorted_objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)

        # Return the latest object
        return sorted_objects[0]

    except ClientError as e:
        print(f"Error retrieving objects from S3: {e}")
        return None


def get_latest_2_object_from_s3(bucket_name: object, subdirectory: object) -> object:
    """
    Retrieve the latest object from a specific subdirectory in the S3 bucket based on the LastModified date.
    """
    try:
        # List all objects in the subdirectory (using Prefix to simulate a subdirectory)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=subdirectory)

        # Check if the subdirectory is empty
        if 'Contents' not in response:
            print(f"No objects found in the subdirectory: {subdirectory}")
            return None

        # Sort objects by the LastModified date to get the latest one
        sorted_objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)

        # Return the latest object
        return sorted_objects[0], sorted_objects[1]

    except ClientError as e:
        print(f"Error retrieving objects from S3: {e}")
        return None
    except IndexError as e:
        print(f"Error retrieving objects from S3: {e}")
        return None


def archive_site_in_s3(bucket_name, key, url):
    try:
        response = requests.get(url)

        response.raise_for_status()  # Raise error for bad responses (4xx or 5xx)

        # Create a unique S3 key using timestamp and the URL domain
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')

        s3_key = f"{key}_{timestamp}.html"

        # Upload content to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=response.content,
            ContentType='text/html'
        )

        return f"Website archived successfully at s3://{bucket_name}/{s3_key}"
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch the website: {e}"


def get_html_body_from_s3(bucket_name, key):
    """
    Retrieve the HTML content of an S3 object.
    """
    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=key
        )
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        print(f"Error retrieving object from S3: {e}")
        return None,


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


def is_site_updated(event):
    try:
        sns_message = event['Records'][0]['Sns']['Message']
        print(f"Received SNS message: {sns_message}")
        return sns_message is not None
    except KeyError:
        return False
