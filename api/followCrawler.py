import urllib3
import certifi
import json
import urllib.parse as urlparse
from urllib.parse import urlencode
import time
import os
import csv

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where())

f = open("./api_key", 'r')
API_KEY = f.readline()
f.close()

def build_get_follow_url(user_id, from_to):
    url = "https://api.twitch.tv/helix/users/follows?first=100&"
    from_to_param_name = ""
    if from_to == "both":
        url = url + "from_id=" + str(user_id[0]) + "&to_id=" + str(user_id[1])
        return url
    if from_to == "from":
        from_to_param_name = "from_id"
    else:
        from_to_param_name = "to_id"
    url = url + from_to_param_name + "=" + str(user_id)
    return url

def change_url_pagination(url, pagination):
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    if not 'cursor' in pagination.keys():
        return 'no result'
    query['after'] = pagination['cursor']
    url_parts[4] = urlencode(query)
    return urlparse.urlunparse(url_parts)

# get top 500 follows (리퀘스트 너무 많이 보내면 거절당해서 500개만 가져옴)
# if from_to == "from", get ids 'user following'
# if from_to == "to", get ids 'following user'
# if from_to == "both", if user_id[0] follows user_id[1] return user_id[0]
#                       , else return an empty list
def getFollows(user_id, from_to):
    follows = list()
    url = build_get_follow_url(user_id, from_to)
    header = {'Client-ID': API_KEY}
    response = http.request(
        'GET',
        url,
        headers = header
    )
    response_dict = json.loads(response.data.decode('utf-8'))
    total = response_dict["total"]
    data = response_dict["data"]
    for follow_info in data:
        follows.append(follow_info["from_id"])
    pagination = response_dict["pagination"]

    loop_count = (int(total)-1)//20
    if loop_count > 99:
        loop_count = 99
    for loop_iterator in range(loop_count):
        time.sleep(30)
        url = change_url_pagination(url, pagination)
        if url == 'no result':
            break
        # if there is no timeout, response will be 429 (too many request)
        response = http.request(
            'GET',
            url,
            headers = header
        )
        response_dict = json.loads(response.data.decode('utf-8'))
        print('#' + str(loop_iterator + 1))
        print(response_dict)
        total = response_dict["total"]
        data = response_dict["data"]
        for follow_info in data:
            follows.append(follow_info["from_id"])
        pagination = response_dict["pagination"]
    return follows

def getApikey():
    return API_KEY

# streamer name -> id
def get_id_by_name(name):
    url = "https://api.twitch.tv/helix/users?login=" + name
    header = {'Client-ID': API_KEY}
    response = http.request(
        'GET',
        url,
        headers = header
    )
    response_dict = json.loads(response.data.decode('utf-8'))
    data = response_dict["data"]
    return data[0]["id"]

def getStreamerNames():
    path = os.path.join(os.getcwd(), "../data")
    return [dI for dI in os.listdir(path) if os.path.isdir(os.path.join(path,dI))]


streamerNames = getStreamerNames()
#streamers = {}
for name in streamerNames:
    id = get_id_by_name(name)
    #streamers[name] = get_id_by_name(name)
    follows = getFollows(id, 'to')
    with open(os.path.join(os.getcwd(), 'follows_' + name + ".txt"), 'w+', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_NONE)
        wr.writerow(follows)
