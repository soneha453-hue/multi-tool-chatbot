
#**********************************imports*******************************************************************
from langgraph.graph import StateGraph,START,END
from typing import TypedDict ,Annotated
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun,WikipediaQueryRun
from  langchain_core.messages import BaseMessage,HumanMessage,SystemMessage,trim_messages
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import  tool
import sqlite3 
import requests
import random
import ast
import operator
import os 
os.environ["LANGCHAIN_PROJECT"] = "multi-tool-chatbot"



conn=sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer=SqliteSaver(conn=conn)

load_dotenv()
#*********************************************LLM*********************************************************

llm = ChatGroq(model='openai/gpt-oss-120b')

#**********************************************system prompt*********************************************
system_prompt = """You are an intelligent AI assistant.

## Communication Style
- Give the answer first.
- Use structure only when it improves readability.
- Avoid unnecessary headings, tables, and long explanations.
- Keep responses clean, modern, and easy to scan.
- Prefer natural language over rigid templates.
- Match the user's language (Hindi, English, Hinglish).

## Formatting Rules
Use the smallest format that communicates clearly:
- One-line question → one-line answer.
- Simple explanation → short paragraphs or bullets.
- Comparison → compact table.
- Process → numbered steps.
- Complex topics → progressive explanation (simple → detailed).
- Always use proper markdown formatting.
- Use ## for headings when needed.
- Use **bold** for important terms.
- Use tables when comparing data.
- Use ``` for code blocks.

## Tool Usage
Always use available tools when they can improve accuracy:
- Weather → get_weather_info tool
- Stocks → get_stockprice tool
- Math → calculator tool
- Current information → tavily_tool ans search 
Never say "I cannot retrieve" — always use the tool.
Never mention tool names unless the user asks.

## Search Results Rule
- From search results, extract ONLY the direct answer.
- Maximum 3-4 lines from any search result.
- Never show URLs unless user specifically asks.
- Never show raw tables from search results — convert to clean readable format.

## What To Avoid
- Don't force sections like "Summary", "Conclusion", or "Recommendation".
- Don't add filler text.
- Don't repeat the question.
- Don't write walls of text.
- Don't use excessive emojis.
- Don't dump raw search results.

Think like a knowledgeable human expert, not a report generator.
"""
#************************************************Tools******************************************************


tavily_tool = TavilySearch(max_results=3)

@tool
def search(query: str) -> str:
    """Search for current information, news, and general knowledge."""
    results = tavily_tool.invoke(query)
    
    output_parts = []
    if results.get('answer'):
        output_parts.append(results['answer'])
    
    result_list = results.get('results', [])
    if not result_list:
        return "No relevant search results found."
    
    for r in result_list[:3]:
        content = r.get('content', '').strip()
        if content:
            output_parts.append(f"Source: {r.get('title','')}\n{content}")
    
    if not output_parts:
        return "No relevant search results found."
    
    return "\n\n".join(output_parts)

OPERATORS={
    ast.Add : operator.add,
    ast.Sub : operator.sub,
    ast.Mult: operator.mul,
    ast.Div : operator.truediv,
    ast.Mod :operator.mod,
    ast.Pow :operator.pow,
    ast.USub :operator.neg
}

def sava_eval(node):
    if isinstance(node,ast.Constant):
        return node.value
    elif isinstance(node,ast.BinOp):
        left=sava_eval(node.left)
        right=sava_eval(node.right)
        op=OPERATORS[type(node.op)]
        return op(left,right)
    elif isinstance(node,ast.UnaryOp):
        return  OPERATORS[type(node.op)](sava_eval(node.operand))
    else:
        raise ValueError("Unsupported operation")
    

@tool
def calculator(expression:str)->str:
    """ Use this tool when user asks any mathematical calculation.
    Input should be a valid math expression string.
    Examples: '2 + 3', '10 * 5', '(100 - 20) / 4', '2 ** 8'
    Supports: +, -, *, /, **, %
    """

    try:
        tree=ast.parse(expression,mode='eval')
        result=sava_eval(tree.body)

        return str(result)
    except Exception as e:
        return f" error {e}"
    

@tool
def get_stockprice(symbol:str)->str:
    """Get current stock price for a given symbol.
    Use for any stock price related questions.
    Example symbols: 'AAPL' for Apple, 'RELIANCE.NS' for Reliance India, 'TCS.NS' for TCS
    """
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={os.getenv('FINNHUB_API_KEY')}"
    response =requests.get(url)
    data= response.json()
    return  f"Current price: {data['c']}, High: {data['h']}, Low: {data['l']}"



@tool 
def get_weather_info(city: str):
    """Use this tool to get current weather information for any city.
    Use when user asks about weather, temperature, humidity, or climate of a place.
    Input should be a city name string.
    Examples: 'London', 'Mumbai', 'New York', 'Delhi,UP'
    Returns current temperature, weather condition, humidity and wind speed.
    """
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv("OPENWEATHER_API_KEY")}&units=metric'
    response = requests.get(url)
    data = response.json()

    if str(data.get('cod')) != '200':
        return f"Weather fetch failed: {data.get('message', 'unknown error')}"

    return (
        f"City: {city}, "
        f"Temp: {data['main']['temp']}°C, "
        f"Condition: {data['weather'][0]['description']}, "
        f"Humidity: {data['main']['humidity']}%, "
        f"Wind: {data['wind']['speed']} m/s"
    )

#**************************************tools Function with llms******************************************************

tools=[search,get_stockprice,get_weather_info,calculator]
 


llm_with_tools=llm.bind_tools(tools)
#*********************************************************State***********************************************
class chatState(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]

#***************************************************chat node*************************************************

def chat_node(state:chatState):
    messages=state['messages']

    trim_msg=trim_messages(
        messages,
        max_tokens=20,
        strategy='last',
        token_counter=len,
        include_system=False,
        allow_partial=False
    )
    final_message=[SystemMessage(content=system_prompt)]+trim_msg
    response=llm_with_tools.invoke(final_message)

    return {'messages':[response]}


tool_node=ToolNode(tools,handle_tool_errors=True)

#****************************************************graph and edges*********************************************

graph=StateGraph(chatState)

graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')
graph.add_edge('chat_node',END)

chatbot=graph.compile(checkpointer=checkpointer)

#**********************************************Dynamic thread****************************************************

def retriev_thread():
    all_thread=set()
    for chackpointer in checkpointer.list(None):
        all_thread.add(chackpointer.config['configurable']['thread_id'])

    return list(all_thread)

#***************************************************delete thread_function****************************************

def delete_thread(thread_id):
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    conn.commit()



# chatbot
# config={'configurable':{'thread_id':'threa_id-4'}}



# out=chatbot.invoke({'messages':[HumanMessage(content='what stock price of apple ')]},config=config)
# print(out['messages'][-1].content)