from dotenv import load_dotenv
import os
import requests
from urllib.parse import quote_plus
from snapshots_operations import poll_snapshot_status,download_snapshot
load_dotenv()

API_KEY = os.getenv('API_KEY')
dataset_id = "gd_lvz8ah06191smkebj4"
#To define the api request 
def _make_api_requests(url,**kwargs):
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    headers = {

        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
         response = requests.post(url, headers=headers,**kwargs)
         #when there is any errors raise the error
         response.raise_for_status()
         return response.json()
    except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
    except Exception as e:
          print(f"Unkonwn error {e}")
          return None
# function to search for three websites google, bing, reddit
def serp_search(query, engine="google"):
       if engine == "google":
             base_url = "https://www.google.com/search"
       elif engine == "bing":
             base_url = "https://www.bing.com/search"        
       else:
            raise ValueError(f"Unknown engine {engine}")     
       url= "https://api.brightdata.com/request"
       payload = {
             "zone": "search_ai",
             "url":f"{base_url}?q={quote_plus(query)}&brd_json=1",
             "format":"raw" 
       }
       full_response = _make_api_requests(url,json=payload)
       if not full_response:
             return None
       #Not extracted the all data
       extracted_data = {
             "knowledge": full_response.get("knowledge",{}),
             "organic": full_response.get("organic",[])

       }
       return extracted_data

def trigger_url_and_download_snapshots(trigger_url, data,params, operation_name="operation"):
      trigger_results = _make_api_requests(trigger_url,params=params,json=data)
      if not trigger_results:
            return None
      snapshot_id=trigger_results.get("snapshot_id")
      if not snapshot_id:
            return None
    
      #poll snap shots
      if not poll_snapshot_status(snapshot_id):
            return None
      raw_data=download_snapshot(snapshot_id)
      return raw_data

def reddit_search_api(keyword,date="All time",sort_by="Hot",num_of_posts=10):
      trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
      params = {
           "dataset_id":dataset_id,
           "include_errors":"true",
           "type":"discover_new",
           "discover_by":"keyword"
           }
      data = [

            {
                  "keyword":keyword, 
                  "date":date,
                  "sort_by":sort_by,
                  "num_of_posts":num_of_posts
            }
      ]
      raw_data=trigger_url_and_download_snapshots(trigger_url=trigger_url,data=data,params=params,operation_name="reddit")
      if not raw_data:
            return None
      parsed_data = []
      for post in raw_data:
           parsed_post =  {
            "title":post.get("title"),
             "url": post.get("url")
            }
           parsed_data.append(parsed_post)
      return {"parsed_posts":parsed_data,"total":len(parsed_data)}    


def reddit_retrieval_posts(urls,days_back,comment_limit=" ",load_all_replies="false"):
    if not urls:
          return None
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {
           "dataset_id":"gd_lvzdpsdlw09j6t702",
           "include_errors":"true"
           }
   
    data = [
          {
          "url":url,
          "days_back":days_back,
          "load_all_replies":load_all_replies,
          "comment_limit":comment_limit}
          for url in urls
    ]
    raw_data=trigger_url_and_download_snapshots(trigger_url=trigger_url,data=data,params=params,operation_name="reddit comment")
    if not raw_data:
           return None
    parsed_comments = []
    for content in raw_data:
          parsed_comment= {
                "comment_id": content.get("comment_id"),
                "comment":content.get("comment"),
                "date_posted": content.get("date_posted"),
                "post_title": content.get("post_url").split("/")[-2] if content.get("post_url").split("/")[-1]=='' else content.get("post_url").split("/")[-1],
                "parent_comment_id": content.get("parent_comment_id")

                }
          parsed_comments.append(parsed_comment)    
    return {"comments":parsed_comments,"total_retrieved":len(parsed_comments)}      
"""
# function to search for three websites google, bing, reddit
def serp_search(query, engine="google"):
       api_key = os.getenv("SCRAPING_DOG_API_KEY")
       if engine == "google":
            base_url = "https://api.scrapingdog.com/google"
            domain = "google.com"
            params = {
                "api_key":f"{api_key}",
                "query": f"{query}",
                "results": 10,
                "country": "us",
                "advance_search": "true",
                "domain": f"{domain}"
                }
            response = requests.get(base_url,params=params)
            return response.text
       elif engine == "bing":
            base_url="https://api.scrapingdog.com/scrape"
            response = requests.get(base_url, params={
                  'api_key': f'{api_key}',
                  'url': f'https://www.bing.com/search?q={query}',
                  'dynamic': 'false',
                  })

            return response.text
       else:
            raise ValueError(f"Unknown engine {engine}")     
      
       #print(response.json())
       #full_response = response.json()
"""       
       
      

          