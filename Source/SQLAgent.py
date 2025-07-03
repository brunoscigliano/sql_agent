import json
from Source.SystemMessages import get_sql_agent_system_message

class SQLAgentWithTools:
    """SQL Agent that uses OpenAI function calling with SQL tools"""
    
    def __init__(self, openai_client, agent_tools, model="gpt-4o", debug_mode: bool = False):
        self.client = openai_client
        self.agent_tools = agent_tools
        self.model = model
        self.debug_mode = debug_mode
        self.available_functions = agent_tools.get_available_functions()
    
    def execute_function_call(self, function_name: str, arguments: dict) -> str:
        """Execute a function call with the given arguments"""
        if function_name in self.available_functions:
            function = self.available_functions[function_name]
            try:
                if function_name == "list_sql_database":
                    return function()
                else:
                    return function(**arguments)
            except Exception as e:
                return json.dumps({"error": str(e)})
        else:
            return json.dumps({"error": f"Function {function_name} not found"})
    
    def ask(self, question: str, max_iterations: int = 20) -> str:
        """Ask a question and let the agent use tools to answer it"""
        
        messages = [
            {
                "role": "system", 
                "content": get_sql_agent_system_message()
            },
            {"role": "user", "content": question}
        ]
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Make API call with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.agent_tools.get_tools_definition(),
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            messages.append(response_message)
            
            # Check if the model wants to call functions
            if response_message.tool_calls:
                # Execute each function call
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if self.debug_mode:
                        print(f"DEBUG: 🔧 Calling {function_name} with args: {function_args}")
                    
                    # Execute the function
                    function_response = self.execute_function_call(function_name, function_args)
                    
                    # Add function response to messages
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response
                    })
            else:
                # No more function calls, return the final response
                return response_message.content
        
        return "Maximum iterations reached. Please try a simpler question."