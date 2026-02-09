from typing import List, Dict, Any, Optional
import google.generativeai as genai
import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

class SQLGenerator:
    """
    Generates SQL queries from natural language questions using Gemini.
    """
    
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("GEMINI_API_KEY not found. SQL Generation will be disabled.")
            self.model = None

    def _get_schema_context(self) -> str:
        """
        Constructs a schema context string from the catalog.
        For MVP, we will focus on the 'marketing_warehouse' or active dataset.
        """
        # Retrieve all tables and columns
        # This can be optimized to only include relevant tables based on keywords
        schema_text = "BigQuery Schema:\n"
        
        # Simplify: just dump all tables and columns from catalog
        # In production, we'd use vector search to find relevant tables.
        for table in self.catalog_service.tables.values():
            schema_text += f"Table: {table.id} (description: {table.description or ''})\n"
            columns = self.catalog_service.list_columns(table.id)
            for col in columns:
                schema_text += f"  - {col.name} ({col.datatype})\n"
            schema_text += "\n"
            
        return schema_text

    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generates a BigQuery SQL query from a natural language question.
        Returns a dict with 'sql' and 'explanation'.
        """
        if not self.model:
            return {"error": "LLM Service not initialized (missing API Key)"}

        schema_context = self._get_schema_context()
        
        prompt = f"""
You are an expert BigQuery SQL generator.
Your goal is to convert the user's natural language question into a valid Standard SQL query for BigQuery.

{schema_context}

Rules:
1. ONLY return the SQL query. No markdown formatting, no backticks.
2. Use standard SQL syntax (BigQuery).
3. If the user asks for "revenue", look for columns like 'amount', 'price', 'value' in transaction tables.
4. If the user asks for "churn", look for 'subscription_status' or 'churned' flags.
5. Today's date is CURRENT_DATE().

Question: {question}

SQL:
"""
        try:
            response = self.model.generate_content(prompt)
            sql = response.text.strip().replace("```sql", "").replace("```", "")
            return {
                "sql": sql,
                "explanation": "Generated from schema context."
            }
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return {"error": str(e)}
