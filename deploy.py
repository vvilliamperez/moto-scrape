"""
This script uploads a deployment package to an S3 bucket and updates an AWS Lambda function with the new code.
You need to have the AWS CLI installed and configured with the necessary permissions to update the Lambda function.
Your .aws/credentials file should contain the necessary access keys.
"""

import os
import uuid

import boto3
from botocore.exceptions import ClientError

S3_BUCKET = "moto-scraper"
LAMBDA_FUNCTION_NAME = "scrapeAf1"
DEPLOYMENT_PACKAGE = "my_deployment_package.zip"

AWS_PROFILE = "AdministratorAccess-986354456027"
AWS_REGION = "us-east-1"


session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)



def upload_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket."""
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = session.client("s3")
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"File {file_name} uploaded to S3 bucket {bucket} successfully.")
    except ClientError as e:
        print(f"Failed to upload {file_name} to S3: {e}")
        return None

    # Return the S3 URI
    return f"s3://{bucket}/{object_name}"


def update_lambda_function(lambda_function_name, s3_bucket, s3_key):
    """Update the AWS Lambda function's code with the deployment package in S3."""
    lambda_client = session.client("lambda")

    try:
        response = lambda_client.update_function_code(
            FunctionName=lambda_function_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key,
            Publish=True,  # Automatically publish a new version
        )
        print(f"Lambda function {lambda_function_name} updated successfully.")
        return response
    except ClientError as e:
        print(f"Failed to update Lambda function: {e}")
        return None


if __name__ == "__main__":
    # Ensure the deployment package exists
    package_to_deploy = os.path.join(os.getcwd(), "scrapeAf1")
    os.chdir(package_to_deploy)

    if not os.path.exists(DEPLOYMENT_PACKAGE):
        print(
            f"Error: {DEPLOYMENT_PACKAGE} not found. Please create the deployment package first."
        )
        exit(1)

    # Step 1: Upload the deployment package to S3
    # Generate unique key for the deployment package using a uuid
    s3_key = "build/" + f"package-{uuid.uuid4()}.zip"
    s3_uri = upload_to_s3(DEPLOYMENT_PACKAGE, S3_BUCKET, s3_key)
    if not s3_uri:
        print("Error: Upload to S3 failed.")
        exit(1)

    print(f"Deployment package uploaded to: {s3_uri}")

    # Step 2: Update the Lambda function code with the S3 URI
    response = update_lambda_function(LAMBDA_FUNCTION_NAME, S3_BUCKET, s3_key)
    if response:
        print("Lambda function updated successfully.")
    else:
        print("Error: Failed to update the Lambda function.")
