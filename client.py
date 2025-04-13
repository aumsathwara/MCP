import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv
import os 

load_dotenv()  

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

client = genai.Client(api_key=GEMINI_API_KEY)

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = client

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
    
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])


    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        
        response = await self.session.list_tools()
        
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": tool.inputSchema.get("type", "object"),  
                "properties": {
                    key: {
                        "type": val.get("type", "string"),  
                        "description": val.get("description", "No description available")  
                    }
                    for key, val in tool.inputSchema.get('properties', {}).items()
                },
                "required": tool.inputSchema.get('required', [])  
            }
        } for tool in response.tools]

        available_tools = types.Tool(function_declarations=[tool for tool in available_tools])
        config = types.GenerateContentConfig(tools=[available_tools])
        contents = [message["content"] for message in messages]

        # Initial gemini call
        response = self.anthropic.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []
        
        # Process the response
        for candidate in response.candidates:
            # Extract the content from the candidate response
            content = candidate.content
            # Iterate through parts inside the content
            for part in content.parts:
                # Case 1: If there is a function call (tool use) in this part
                if hasattr(part, 'function_call') and part.function_call:
                    tool_name = part.function_call.name
                    tool_args = part.function_call.args
                    
                    # Execute the tool call (this assumes the tool function is properly defined)
                    result = await self.session.call_tool(tool_name, tool_args)
                    list_result = json.loads([i for i in result.content[0]][1][1])['text']

                    # Append the result of the tool call to tool_results
                    tool_results.append({"call": tool_name, "result": result})
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                    
                    print(f"\nResults: {list_result}")
                    
                    # If the part also has text (after tool call), append it to the conversation
                    if hasattr(part, 'text') and part.text:
                        messages.append({
                            "role": "assistant",
                            "content": part.text
                        })
                    
                    # Add the result content from the tool call as the next user's message
                    messages.append({
                        "role": "user", 
                        "content": list_result
                    })
                    
                # Case 2: If there is no function call (just a regular text response)
                elif hasattr(part, 'text') and part.text:
                    final_text.append(part.text)
                    messages.append({
                        "role": "assistant",
                        "content": part.text
                    })

            # Append the AI's response (either from a tool call or regular text)
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content.parts and candidate.content.parts[0].text:
                        final_text.append(candidate.content.parts[0].text)

        return "\n".join(final_text)


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()



async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()



if __name__ == "__main__":
    import sys
    asyncio.run(main())