import json
import boto3
import glob
import subprocess
import lambdautils
import decimal
import time
from botocore.client import Config
from boto3.dynamodb.types import DYNAMODB_CONTEXT

# Inhibit Inexact Exceptions
DYNAMODB_CONTEXT.traps[decimal.Inexact] = 0
# Inhibit Rounded Exceptions
DYNAMODB_CONTEXT.traps[decimal.Rounded] = 0
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
db_name = 'jg-page-relation'
table = dynamodb.Table(db_name)

config = json.loads(open('driverconfig.json', 'r').read())

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

bucket = config["bucket"]
region = config["region"]
pages = s3_client.get_object(Bucket=bucket, Key=config["pages"])


# page들의 관계 데이터셋을 만들어 반환하는 함수 입니다.
def get_page_relation(pages):
    page_relations = {}
    pages = pages['Body'].read().decode()
    lines = pages.split("\n")
    for line in lines:
        try:
            key = line.split("\t")[0]
            value = line.split("\t")[1]
            value = value.replace("\r", "")
            if key not in page_relations:
                page_relations[key] = []
            if value not in page_relations[key]:
                page_relations[key].append(value)
            print(key, value)
        except:
            pass

    return page_relations


def dynamodb_remove_all_items():
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={
                'page': each['page']
            })


# DynamoDB에 있는 모든 값을 지웁니다.
dynamodb_remove_all_items()
# page의 관계들이 담겨있는 파일을 가지고 dictionary 관계 데이터셋을 만듭니다.
page_relations = get_page_relation(pages)

# DynamoDB에 page relation 업로드
for page in page_relations:
    table.put_item(
        Item={
            'page': str(page),
            'relation': page_relations[page]
        }
    )
