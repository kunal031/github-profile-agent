import os
import asyncio
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mistralai.client import Mistral


# Load credentials from .env
load_dotenv()

# Define the GitHub MCP Server connection structure
server_params = StdioServerParameters(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "ghcr.io/github/github-mcp-server"
    ],
    env=None
)

async def run_agent():
    # 1. Establish the communication channel with the GitHub MCP server
    print("⏳ Launching and connecting to GitHub MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize protocol and pull the active tools schema
            await session.initialize()
            tools_list = await session.list_tools()
            available_tools = {tool.name: tool for tool in tools_list.tools}
            
            print(f"✅ Connected! Discovered {len(available_tools)} available tools.")
            
            mistral_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in tools_list.tools]

            mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
            MODEL_NAME = "mistral-large-latest" 


            print("\n🤖 Chatbot Ready! Type 'exit' to quit.")
            while True:
                user_query = input("\n💬 Your Query (e.g., 'Summarize README of facebook/react'): ")
                if user_query.strip().lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                if not user_query.strip():
                    continue

                # Ask the LLM how to solve the query using the tools
                response = mistral_client.chat.complete(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an expert GitHub assistant. You analyze repositories on demand using your tools."},
                        {"role": "user", "content": user_query}
                    ],
                    tools=mistral_tools,
                    tool_choice="auto"
                )

                tool_calls = response.choices[0].message.tool_calls
                
                # Handle Tool Executions if requested by the LLM
                if tool_calls:
                  for tool_call in tool_calls:
                      name = tool_call.function.name
                      args = tool_call.function.arguments
                      if isinstance(args, str):
                          args = json.loads(args)
                      
                      print(f"⚙️  Mistral selected tool: {name} with arguments: {args}")
                      
                      try:
                          # Forward request to local GitHub Docker container
                          result = await session.call_tool(name, arguments=args)
                          
                          # Extract string content from MCP TextContent objects cleanly
                          raw_content = ""
                          if hasattr(result, 'content') and result.content:
                              raw_content = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                          else:
                              raw_content = str(result)
                                          
                          # Give the raw GitHub data back to the LLM for a polished human response
                          final_response = mistral_client.chat.complete(
                              model=MODEL_NAME,
                              messages=[
                                  {"role": "user", "content": user_query},
                                  response.choices[0].message,  
                                  {
                                      "role": "tool",
                                      "name": name,
                                      "content": raw_content,
                                      "tool_call_id": tool_call.id if hasattr(tool_call, 'id') else None
                                  }
                              ]
                          )
                          print(f"\n💡 Answer:\n{final_response.choices[0].message.content}")
                          
                      except Exception as tool_err:
                          print(f"❌ Failed to run tool {name}: {tool_err}")
                else:
                    # If no tools were required, just print the direct text answer
                    print(f"\n💡 Answer:\n{response.choices[0].message.content}")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting safely.")
