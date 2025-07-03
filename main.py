# main.py
# Main entry point for the SQL agent application
from dotenv import load_dotenv
from openai import OpenAI
from Source.SQLAgent import SQLAgentWithTools
from Source.AgentTools import AgentTools

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    client = OpenAI()

    tools = AgentTools(client, db_path="chinook.db")

    sql_agent = SQLAgentWithTools(client, tools, debug_mode=True)

    while True:
        user_input = input("Enter a question: ")
        if user_input.lower() == "exit":
            break
        result = sql_agent.ask(user_input)
        print(result)