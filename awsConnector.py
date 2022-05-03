import boto3
import pandas as pd
import os
import logging

from botocore.client import BaseClient
from botocore.exceptions import ClientError

s3 = boto3.resource(
    service_name='s3',
    region_name='ap-south-1',
    aws_access_key_id='AKIAQG3GQ375EVELY2ZL',
    aws_secret_access_key='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'
)

# s3_client = boto3.client(service_name='s3',
#                          region_name='ap-south-1',
#                          aws_access_key_id='AKIAQG3GQ375EVELY2ZL',
#                          aws_secret_access_key='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')  # Use LocalStack Endpoint

# for bucket in s3.buckets.all():
#     print(bucket.name)

# # Make dataframes
# foo = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
# bar = pd.DataFrame({'x': [10, 20, 30], 'y': ['aa', 'bb', 'cc']})
#
# # Save to csv
# foo.to_csv('trisl.csv')
# bar.to_csv('bar.csv')


# s3.Bucket('vk26bucket').upload_file(Filename='foo.csv', Key='cv/olp.csv')
# s3.Bucket('vk26bucket').upload_file(Filename='bar.csv', Key='bar.csv')


def upload_file_to_bucket(file_obj, bucket, folder, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_obj

    print("i am here")
    # Upload the file
    print(bucket)
    print(file_obj)
    print(f"{folder}/{object_name}")
    print("i am here 2")

    try:
        # with open("files", "rb") as f:
        s3.Bucket(bucket).upload_fileobj(file_obj, Key=f"{folder}/{object_name}")

    # s3_client.upload_fileobj(file_obj, bucket, f"{folder}/{object_name}")
    except ClientError as e:
        logging.error(e)
        return False
    return True



