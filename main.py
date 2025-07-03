# main.py
# Main entry point for the SQL agent application
from dotenv import load_dotenv
from openai import OpenAI
from Source.SQLAgent import SQLAgentWithTools
from Source.AgentTools import AgentTools
from Source.ChromaClient import ChromaCollectionFactory

load_dotenv()

if __name__ == "__main__":
    client = OpenAI()
    vector_store = ChromaCollectionFactory.create_collection(db_path="chinook.db")
    tools = AgentTools(client, db_path="chinook.db", vector_store=vector_store)

    sql_agent = SQLAgentWithTools(client, tools, debug_mode=True)

    while True:
        user_input = input("Enter a question: ")
        if user_input.lower() == "exit":
            break
        result = sql_agent.ask(user_input)
        print(result)