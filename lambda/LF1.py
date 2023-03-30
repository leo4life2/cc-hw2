import json
import logging
import boto3
import datetime
import urllib3

def log(message):
    logging.info(str(message))
    print(str(message))
    
def getUploadedLabels(bucket, key):
    s3 = boto3.client('s3')
    response = s3.head_object(Bucket=bucket, Key=key)
    
    # May not exist, in that case return empty list
    customLabels = response['ResponseMetadata']['HTTPHeaders'].get('x-amz-meta-customlabels', [])
    if customLabels:
        customLabels = customLabels.split(",")
        
    return customLabels
    
def getRekogLabels(bucket, key):
    rekognition = boto3.client('rekognition')
    
    response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    
    return [label['Name'] for label in response['Labels']]

def addESObject(bucket, key, labels):
    current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    es_document = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": current_time,
        "labels": labels
    }

    es_host = 'vpc-photos-hmbxw6uzgzlotjo7woakutktha.us-east-1.es.amazonaws.com'
    es_base_url = f'https://{es_host}'

    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='master:Master!@#123')
    headers['Content-Type'] = 'application/json'

    # Check if the 'photos' index exists
    log("Check if photos index exists")
    response = http.request('HEAD', f'{es_base_url}/photos', headers=headers)

    if response.status == 404:
        # Create the 'photos' index
        log("Create photos index")
        response = http.request('PUT', f'{es_base_url}/photos', headers=headers)
        response.status

    # Index the document
    log("Indexing document")
    response = http.request('POST', f'{es_base_url}/photos/_doc', headers=headers, body=json.dumps(es_document))
    response.status

    log("ES added object.")

    query = {
        "query": {
            "match_all": {}  # This is an example query that matches all documents in the index
        }
    }

    # Perform the search
    response = http.request('GET', f'{es_base_url}/photos/_search', headers=headers, body=json.dumps(query))

    search_results = json.loads(response.data)
    log("ES query all result is " + str(search_results))

    
def delete_all_documents_in_photos_index():
    es_host = 'vpc-photos-hmbxw6uzgzlotjo7woakutktha.us-east-1.es.amazonaws.com'
    es_base_url = f'https://{es_host}'

    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='master:Master!@#123')
    headers['Content-Type'] = 'application/json'

    # Delete all documents in the 'photos' index
    query = {
        "query": {
            "match_all": {}  # This is an example query that matches all documents in the index
        }
    }
    response = http.request('POST', f'{es_base_url}/photos/_delete_by_query', headers=headers, body=json.dumps(query))
    response_data = json.loads(response.data)
    log("Deleted documents count: " + str(response_data["deleted"]))

def lambda_handler(event, context):
    log("Event is: " + str(event))

    BUCKET='cc-photos-b2'
    newObjKey = event['Records'][0]['s3']['object']['key']
    
    uploaded_labels = getUploadedLabels(BUCKET, newObjKey)
    rekog_labels = getRekogLabels(BUCKET, newObjKey)
    all_labels = uploaded_labels + rekog_labels
    
    addESObject(BUCKET, newObjKey, all_labels)
    
    # delete_all_documents_in_photos_index()
    
    return {
        'statusCode': 200,
        'body': json.dumps('Everything done')
    }
