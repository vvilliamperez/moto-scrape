import requests
import hashlib
import boto3
import urllib.parse

from botocore.exceptions import ClientError

s3_client = boto3.client('s3')


def url_to_s3_path(url):
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

    return s3_friendly_path


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


def get_site_hash(url):
    response = requests.get(url)
    content = response.text
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_latest_hash(url, bucket):
    key = url_to_s3_path(url)
    get_latest_object_from_s3(bucket, key)


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


