import json
import sqlite3
import pandas as pd
from openai import OpenAI
from typing import Dict, Any, List
from SystemMessages import get_sql_checker_system_message

class AgentTools:
    """SQL Agent Tools that encapsulate database operations and AI-powered validation"""
    
    def __init__(self, client: OpenAI, db_path: str, model: str = "gpt-4o-mini"):
        """
        Initialize AgentTools with OpenAI client and configuration
        
        Args:
            client (OpenAI): OpenAI client instance
            db_path (str): Path to SQLite database
            model (str): GPT model to use (default: "gpt-4o-mini")
        """
        self.client = client
        self.model = model
        self.db_path = db_path
    
    def query_sql_database(self, query: str) -> str:
        """
        Execute a SQL query against the database.
        
        Args:
            query (str): A detailed and correct SQL query to execute
            
        Returns:
            str: JSON string containing query results or error message
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Execute the query and get results as DataFrame
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert to JSON format
            if df.empty:
                return json.dumps({"message": "Query executed successfully but returned no results."})
            
            # Limit results to prevent overwhelming output
            if len(df) > 100:
                result_data = {
                    "message": f"Query returned {len(df)} rows. Showing first 100 rows.",
                    "data": df.head(100).to_dict('records'),
                    "total_rows": len(df)
                }
            else:
                result_data = {
                    "message": f"Query returned {len(df)} rows.",
                    "data": df.to_dict('records'),
                    "total_rows": len(df)
                }
                
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = {
                "error": str(e),
                "message": "Query failed. Please check your SQL syntax and table/column names."
            }
            return json.dumps(error_msg, indent=2)
    
    def info_sql_database(self, tables: str) -> str:
        """
        Get schema information and sample rows for specified tables.
        
        Args:
            tables (str): Comma-separated list of table names
            
        Returns:
            str: JSON string containing schema and sample data for the tables
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            table_list = [table.strip() for table in tables.split(',')]
            result = {"tables": {}}
            
            for table_name in table_list:
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    result["tables"][table_name] = {"error": f"Table '{table_name}' does not exist"}
                    continue
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    schema.append({
                        "column_name": col[1],
                        "data_type": col[2],
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5])
                    })
                
                # Get sample rows (first 3)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_rows = cursor.fetchall()
                
                # Get column names for sample data
                column_names = [desc[0] for desc in cursor.description]
                sample_data = []
                for row in sample_rows:
                    sample_data.append(dict(zip(column_names, row)))
                
                result["tables"][table_name] = {
                    "schema": schema,
                    "sample_rows": sample_data,
                    "row_count": len(sample_data)
                }
            
            conn.close()
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = {
                "error": str(e),
                "message": "Failed to retrieve table information."
            }
            return json.dumps(error_msg, indent=2)
    
    def list_sql_database(self) -> str:
        """
        List all available tables in the database.
        
        Returns:
            str: JSON string containing list of all tables
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            table_names = [table[0] for table in tables]
            
            result = {
                "message": f"Found {len(table_names)} tables in the database",
                "tables": table_names
            }
            
            conn.close()
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = {
                "error": str(e),
                "message": "Failed to list database tables."
            }
            return json.dumps(error_msg, indent=2)
    
    def query_sql_checker(self, query: str) -> str:
        """
        Validate a SQL query for common mistakes before execution.
        
        Args:
            query (str): SQL query to validate
            
        Returns:
            str: JSON string with validation results and corrected query if needed
        """
        try:
            # Use OpenAI to check the query
            system_prompt = get_sql_checker_system_message()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Validate this SQLite query: {query}"}
                ],
                temperature=0.1
            )
            
            # Try to parse the response as JSON
            try:
                content = response.choices[0].message.content
                if content is None:
                    raise json.JSONDecodeError("Empty response", "", 0)
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create a structured response
                result = {
                    "has_errors": False,
                    "errors": [],
                    "corrected_query": query,
                    "explanation": response.choices[0].message.content
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = {
                "error": str(e),
                "message": "Failed to validate query."
            }
            return json.dumps(error_msg, indent=2)
    
    def get_available_functions(self) -> Dict[str, Any]:
        """
        Get dictionary of available functions for tool execution
        
        Returns:
            Dict[str, Any]: Dictionary mapping function names to methods
        """
        return {
            "query_sql_database": self.query_sql_database,
            "info_sql_database": self.info_sql_database,
            "list_sql_database": self.list_sql_database,
            "query_sql_checker": self.query_sql_checker,
        }
    
    @staticmethod
    def get_tools_definition() -> List[Dict[str, Any]]:
        """
        Get OpenAI tools definition for function calling
        
        Returns:
            List[Dict[str, Any]]: List of tool definitions for OpenAI function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_sql_database",
                    "description": "Execute a SQL query against the database. Returns results or error message.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "A detailed and correct SQL query to execute against the database"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "info_sql_database",
                    "description": "Get schema information and sample rows for specified tables. Use list_sql_database first to see available tables.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tables": {
                                "type": "string",
                                "description": "Comma-separated list of table names to get information for (e.g., 'Artist, Album, Track')"
                            }
                        },
                        "required": ["tables"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_sql_database", 
                    "description": "List all available tables in the database.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_sql_checker",
                    "description": "Validate a SQL query for common mistakes before execution. Always use this before executing queries.",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to validate for syntax errors and common mistakes"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ] 