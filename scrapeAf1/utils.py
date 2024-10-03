import requests
import hashlib
import boto3
import urllib.parse
from bs4 import BeautifulSoup

from botocore.exceptions import ClientError

s3_client = boto3.client('s3')


def url_to_s3_path(url, prefix=None):
    # Step 1: Parse the URL
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


def get_site_hash_now(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove dynamic elements
    for tag in soup(['script', 'style']):
        tag.decompose()

    # You can also remove specific dynamic sections based on class or ID
    for dynamic_section in soup.find_all(class_='ad-section'):
        dynamic_section.decompose()

    # Get the main content as text
    main_content = soup.get_text()

    return hashlib.md5(main_content.encode('utf-8')).hexdigest()


def get_latest_hash_in_s3(url, bucket):
    key = url_to_s3_path(url)
    subdirectory = key.split('/')[0]
    subdirectory = 'page_hashes' + '/' + subdirectory
    obj = get_latest_object_from_s3(bucket, subdirectory)
    if not obj:
        return None

    key = obj['Key']
    response = s3_client.get_object(Bucket=bucket, Key=key)

    return response['Body'].read().decode('utf-8')


def store_hash_in_s3(bucket_name, key, hash_value):
    """
    Store the MD5 hash in an S3 object.
    """
    try:
        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=hash_value
        )
        print(f"Successfully stored hash: {hash_value} in S3 under key: {key}")
    except ClientError as e:
        print(f"Error uploading to S3: {e}")


