import json
import boto3
import requests
import uuid

AMAZON_LEX_BOT = "photobot_test"
LEX_BOT_ALIAS = "test_one"
USER_ID = "user"

TABLENAME = 'photos'
ELASTIC_SEARCH_URL = "https://search-photos-k7c4fhun4s6ceugot6xz4efrbu.us-east-1.es.amazonaws.com/photos/photo/_search?q="

S3_URL = "https://photos-cloud-as2.s3.amazonaws.com/"


def post_on_lex(query, user_id=USER_ID):
    """
    Get the user input from the frontend as text and pass
    it to lex. Lex will generate a new response.
    it will return a json response: 
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lex-runtime.html
    """

    client = boto3.client('lexv2-runtime', region_name='us-east-1')

    # Configure bot details
    botId = '67QSQXNGDY'
    botAliasId = 'TSTALIASID'
    localeId = 'en_US'
    # We have used a hardcoded user instance here as was confirmed this was for 1 user
    sessionId = uuid.uuid4().hex
    print(sessionId)

    init_response = client.recognize_text(
        botId=botId,
        botAliasId=botAliasId,
        localeId=localeId,
        sessionId=sessionId,
        text='initialize intent'
    )
    resp_text = 'No matches'
    if (init_response['messages'][0]['content'] == 'intent initialized'):
        response = client.recognize_text(
            botId=botId,
            botAliasId=botAliasId,
            localeId=localeId,
            sessionId=sessionId,
            text=query
        )
        resp_text = response['messages'][0]['content']

    a = resp_text
    b = []
    b = a.split(",")
    c = b[-1].split(" ")
    b = b[:-1]
    if(len(c)>1):
        c.remove("and")
    labels = b + c
    print("labels are below")
    print(labels)
    ans=""
    for x in labels:
        ans+='labels:'+x
    print("ans are below")
    print(ans)
    return ans



def get_photos_ids(URL, labels):
    """
    return photos ids having the 
    labels as desired 
    """

    URL = URL + str(labels)
    print("url is")
    print(URL)
    response = requests.get(URL, auth=("ak9691", "Ak9691-123")).content
    print("Response: ", response)
    data = json.loads(response)
    hits = data["hits"]["hits"]
    id_list = []
    labels_list = []
    for result in hits:
        _id = result["_source"]["objectKey"]
        id_list.append(_id)
        _labels = result["_source"]["labels"]
        labels_list.append(_labels)
    return id_list, labels_list


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
    }


def lambda_handler(event, context):
    query = event['queryStringParameters']['q']

    labels = post_on_lex(query)
    id_list, labels_list = get_photos_ids(ELASTIC_SEARCH_URL, labels)

    results = []
    for i, l in zip(id_list, labels_list):
        results.append({"url": S3_URL + i, "labels": l})

    print(results)
    response = {"results": results}
    return respond(None, response)
