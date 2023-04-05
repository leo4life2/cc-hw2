import json
import logging
import boto3
import datetime
import urllib3

def log(message):
    logging.info(str(message))
    print(str(message))
    
def queryES(keywords):
    es_host = 'vpc-photos-hmbxw6uzgzlotjo7woakutktha.us-east-1.es.amazonaws.com'
    es_base_url = f'https://{es_host}'

    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='master:Master!@#123')
    headers['Content-Type'] = 'application/json'
    
    query = {
        "query": {
            "match_all": {}
        }
    }
    
    if keywords:
        # Union of all keyword matches
        # Demo
        query["query"] = { 
            "bool": {
                "should": [{"match": {"labels": keyword}} for keyword in keywords]
                
            }
        }

    # Perform the search
    response = http.request('GET', f'{es_base_url}/photos/_search', headers=headers, body=json.dumps(query))

    search_results = json.loads(response.data)
    return search_results
    
def lex_parse(user_prompt):
    # Instantiate boto3 client
    client = boto3.client('lexv2-runtime')

    # Get reply from Lex V2 bot
    lex_reply = client.recognize_text(
        botId='PNKZV2BBBW',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='test',
        text=user_prompt,
    )
    
    keywords = []
    for intent in lex_reply["interpretations"]:
        if intent["intent"]["name"] != "SearchIntent":
            continue
        
        slots = intent["intent"]["slots"]
        if slots["keyword"]:
            keywords.append(slots["keyword"]["value"]["interpretedValue"])
        if slots["keyword2"]:
            keywords.append(slots["keyword2"]["value"]["interpretedValue"])
    
    return keywords

""" -- Entry Point --- """
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    log("Event is " + str(event))
    
    try:
    
        raw_prompt = event["queryStringParameters"].get("q", "")
        keywords = []
        if raw_prompt:
            keywords = lex_parse(raw_prompt)
            
        log("keywords is " + str(keywords))
        search_results = queryES(keywords)
        
        result = {
            "results": []
        }
        
        if int(search_results["hits"]["total"]["value"]) > 0:
            for hit in search_results["hits"]["hits"]:
                urlbase = "https://cc-photos-b2.s3.us-east-1.amazonaws.com/"
                obj = {
                    "url": urlbase + hit["_source"]["objectKey"],
                    "labels": hit["_source"]["labels"]
                }
                result["results"].append(obj)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps(result),
            "isBase64Encoded": False
        }
    
    except Exception as e:
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({
                "code": 500,
                "message": str(e)
            }),
            "isBase64Encoded": False
        }