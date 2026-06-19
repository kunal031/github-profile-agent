import os
import datetime
import asyncio
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mistralai.client import Mistral

load_dotenv()



# Configuration for GitHub MCP Server
server_params = StdioServerParameters(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "ghcr.io/github/github-mcp-server"
    ],
    env=None
)

async def run_profile_agent():
    print("⏳ Connecting to GitHub MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # 1. Initialize Tools
            await session.initialize()
            tools_list = await session.list_tools()
            available_tools = {tool.name: tool for tool in tools_list.tools}
            print(f"✅ Tools Ready! (Found {len(available_tools)} GitHub tools)")
            
            # Format tools for Mistral
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

            # 2. Get Target Username
            target_user = input("\n👤 Enter GitHub Username to Analyze (e.g. 'kunal031'): ").strip()
            print(f"\n🔍 Profiling user: {target_user}...")

            # 3. Create a Specialized System Prompt

            today_date = datetime.date.today().strftime("%B %d, %Y")  

            system_instruction = (
              f"You are an expert GitHub Profile Analyst. "
              f"Your goal is to answer questions specifically about the GitHub user '{target_user}'. "
              f"Today's actual current date is {today_date}. {today_date} is NOT the future—it is today. "
              f"When asked about today's activity, search for commits, issues, or push events timestamped with this date. "
              f"When the session starts, try to find out who they are by looking for a repository named '{target_user}/{target_user}' "
              f"or by listing their repositories. Always cite the specific repo or file where you found the information."
            )

            # 4. Chat Loop
            messages = [{"role": "system", "content": system_instruction}]
            
            print(f"💬 Ask anything about @{target_user} (or type 'exit')")
            print("   (Examples: 'What is their tech stack?', 'Summarize their bio', 'List their latest Python projects')")

            while True:
                user_query = input(f"\n❓ Question about @{target_user}: ")
                if user_query.lower() in ['exit', 'quit']:
                    break
                
                # Add user message to history
                messages.append({"role": "user", "content": user_query})

                # --- Tool Execution Loop ---
                while True:
                    # Ask Mistral what to do
                    response = mistral_client.chat.complete(
                        model=MODEL_NAME,
                        messages=messages,
                        tools=mistral_tools,
                        tool_choice="auto"
                    )
                    
                    # Check if Mistral wants to use a tool
                    tool_calls = response.choices[0].message.tool_calls
                    
                    if tool_calls:
                        messages.append(response.choices[0].message) # Add the "intent" to history
                        
                        for tool_call in tool_calls:
                            name = tool_call.function.name
                            args_str = tool_call.function.arguments
                            args = json.loads(args_str) if isinstance(args_str, str) else args_str
                            
                            print(f"   ⚙️  Checking: {name} ({args})")
                            
                            try:
                                # Execute the tool
                                result = await session.call_tool(name, arguments=args)
                                
                                # Format result safely
                                raw_content = ""
                                if hasattr(result, 'content') and result.content:
                                    raw_content = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                                else:
                                    raw_content = str(result)
                                
                                # Feed result back to Mistral
                                messages.append({
                                    "role": "tool",
                                    "name": name,
                                    "content": raw_content,
                                    "tool_call_id": tool_call.id
                                })
                            except Exception as e:
                                print(f"   ❌ Tool Error: {e}")
                                messages.append({
                                    "role": "tool",
                                    "name": name,
                                    "content": f"Error executing tool: {str(e)}",
                                    "tool_call_id": tool_call.id
                                })
                    else:
                        # No more tools needed, print the final answer
                        final_answer = response.choices[0].message.content
                        print(f"\n💡 Analysis:\n{final_answer}")
                        messages.append({"role": "assistant", "content": final_answer})
                        break # Exit the inner loop to wait for next user input

if __name__ == "__main__":
    try:
        asyncio.run(run_profile_agent())
    except KeyboardInterrupt:
        print("\nExiting...")
