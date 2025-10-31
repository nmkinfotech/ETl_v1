import requests
import pandas as pd

def get_hubspot_data(api_key:str, endpoints_list:list):
    api_token ="Bearer " + api_key
    base_url = "https://api.hubapi.com"
    endpoints = endpoints_list
    print(endpoints)
    header={
    "Authorization":api_token
    }

    all_data = {}

    for endpoint in endpoints:
        hasMore= True
        after=None
        params={
            "limit":100
        }        
        endpoint_data=[]
        while hasMore:
            if after:
                params["after"]=after
            response = requests.get(
                url = base_url+endpoint,
                headers=header,
                params=params
            )
            data = response.json()
            endpoint_data.extend(data.get("results",[]))
            paging = data.get("paging")
            if paging and "next" in paging:
                after = paging["next"]["after"]
            else:
                hasMore = False
        all_data[endpoint] = endpoint_data
    return all_data

