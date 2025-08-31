from dotenv import load_dotenv
from typing import Annotated,List
from langgraph.graph import StateGraph, START,END
#each invoke we can add messages or through states
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from web_operations import serp_search,reddit_search_api,reddit_retrieval_posts
from prompts import ( get_bing_analysis_messages,
                      get_google_analysis_messages,
                      get_reddit_analysis_messages,
                      get_reddit_url_analysis_messages,
                      get_synthesis_messages
                     )
load_dotenv()


#by init model the model can access the load_dotenv files
# and use it to access chatgpt
llm = init_chat_model("gpt-4o")


class State(TypedDict):
  #Keep the history of chat between the bot and human
  messages: Annotated[list, add_messages]
  user_question: str| None
  google_results: str| None
  bing_results: str |None
  reddit_results: str| None
  selected_reddit_urls: list[str]|None
  reddit_post_data: list | None
  google_analysis: str | None
  bing_analysis: str | None 
  reddit_analysis: str | None
  final_answer: str|None
class RedditURLFormat(BaseModel):
      selected_urls: List[str] = Field(description="list the reddit urls which are valuable information for answering the user question")
      

def google_search(state:State):
  user_question  =state.get("user_question","")
  print(f"Search Google for: {user_question}")
  google_results = serp_search(query=user_question,engine="google")
  return {"google_results":google_results}

def bing_search(state:State):
  user_question  =state.get("user_question","")
  print(f"Search bing for: {user_question}")
  bing_results = serp_search(query=user_question,engine="bing")
  
  return {"bing_results":bing_results}

def reddit_search(state:State):
  user_question  =state.get("user_question","")
  
  reddit_results = reddit_search_api(user_question)
  print(reddit_results)

  return {"reddit_results":reddit_results}

def analyze_reddit_posts(state:State):
  user_question = state.get("user_question","")
  reddit_result = state.get("reddit_results","")
  if not reddit_result: 
     return {"selected_reddit_urls":[]}
  structured_llm=llm.with_structured_output(RedditURLFormat)
  messages=get_reddit_url_analysis_messages(user_question,reddit_result)
  try: 
      analysis=structured_llm.invoke(messages)
      selecte_urls=analysis.selected_urls
      print("Selected Urls:") 
      for i, url in enumerate(selecte_urls,1):
             print(f"{i}.{url}")
                               

  except Exception as e:
      print(e) 
      selecte_urls  = []


  return {"selected_reddit_urls":selecte_urls}
 
def retireve_reddit_posts(state:State):
  print("Retrieving the reddit comments")
  selected_urls=state.get("selected_urls",[])
  if not selected_urls:
      return {"selected_urls":[]}
  
  print(f"Retrieving from {len(selected_urls)} Reddit Urls")
  reddit_post_data = reddit_retrieval_posts(selected_urls)
  if reddit_post_data:
      print(f"Successfully got {len(reddit_post_data)} post")
  else:
      print("Failed to get the post data")
      reddit_post_data= []
  print(reddit_post_data)    
  return{"reddit_post_data":reddit_post_data}

def analyze_google_results(state:State):
    print("Analyzing google search result...")
    user_question = state.get("user_question","")
    google_results = state.get("google_results","")
    messages=get_google_analysis_messages(user_question,google_results)
    reply=llm.invoke(messages)
    return {"google_analysis":reply.content}

def analyze_bing_results(state:State):
    print("Analyzing bing search result...")
    user_question = state.get("user_question","")
    bing_results = state.get("bing_results","")
    messages=get_bing_analysis_messages(user_question,bing_results)
    reply=llm.invoke(messages)
    return {"bing_analysis":reply.content}

def analyze_reddit_results(state:State):
    print("Analyzing reddit search result...")
    user_question = state.get("user_question","")
    reddit_results = state.get("reddit_results","")
    reddit_retrieval_posts = state.get("reddit_post_data","")
    messages=get_reddit_analysis_messages(user_question,reddit_results,reddit_retrieval_posts)
    reply=llm.invoke(messages)
    return {"reddit_analysis":reply.content}

def synthesize_analyses(state:State):
    user_question = state.get("user_question","")
    google_analysis=state.get("google_analysis","")
    bing_analysis=state.get("bing_analysis","")
    reddit_analysis=state.get("reddit_analysis","")
    messages = get_synthesis_messages(user_question,google_analysis,bing_analysis,reddit_analysis) 
    reply=llm.invoke(messages)
    final_answer=reply.content
    return {"final_answer":reply.content, "messages":[{"role":"assistant","content":final_answer}]}

graph_builder = StateGraph(State)
graph_builder.add_node("google_search",google_search)
graph_builder.add_node("bing_search",bing_search)
graph_builder.add_node("reddit_search",reddit_search)
graph_builder.add_node("analyze_reddit_posts",analyze_reddit_posts)
graph_builder.add_node("retrieve_reddit_posts",retireve_reddit_posts)
graph_builder.add_node("analyze_bing_results",analyze_bing_results)
graph_builder.add_node("analyze_google_results",analyze_google_results)
graph_builder.add_node("analyze_reddit_results",analyze_reddit_results)
graph_builder.add_node("synthesize_analyses",synthesize_analyses)


graph_builder.add_edge(START, "google_search")
graph_builder.add_edge(START, "bing_search")
graph_builder.add_edge(START, "reddit_search")

graph_builder.add_edge("google_search","analyze_reddit_posts")
graph_builder.add_edge("bing_search","analyze_reddit_posts")
graph_builder.add_edge("reddit_search","analyze_reddit_posts")

graph_builder.add_edge("analyze_reddit_posts","retrieve_reddit_posts")
graph_builder.add_edge("retrieve_reddit_posts","analyze_google_results")
graph_builder.add_edge("retrieve_reddit_posts","analyze_bing_results")
graph_builder.add_edge("retrieve_reddit_posts","analyze_reddit_results")
graph_builder.add_edge("analyze_google_results","synthesize_analyses")
graph_builder.add_edge("analyze_bing_results","synthesize_analyses")
graph_builder.add_edge("analyze_reddit_results","synthesize_analyses")
graph_builder.add_edge("synthesize_analyses", END)

graph=graph_builder.compile()


def run_chatbot():
    
    print("Multi-SOurce Research Agent")
    print("Type 'exit' to quit\n")

    while True:
      user_input = input("Ask me anything: ")
      if user_input.lower() == "exit":
           print("Bye")
           break
      state = {
            "messages":[{"role":"user","content":user_input}],
            "user_question": user_input,
            "google_results":None,
            "bing_results":None,
            "reddit_results": None,
            "selected_reddit_urls": None,
            "reddit_post_data":  None,
            "google_analysis":  None,
            "bing_analysis":  None, 
            "reddit_analysis": None,
            "final_answer": None}
      print("\nProcessing mult-search in parallel..")
      print("Lauching Google, Bing, and Reddit searches..\n")
      final_state = graph.invoke(state)
      if final_state.get("final_answer"):
                 print(f"Final answer: {final_state.get("final_answer")}\n")
      print("-"*80)           
if __name__ == "__main__":
      run_chatbot()

