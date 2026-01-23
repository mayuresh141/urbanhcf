import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

class UrbanHCFMCPService:
    def __init__(self):
        load_dotenv()
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

        config_file = "mcp_agent/server/geocode.json"

        self.client = MCPClient.from_config_file(config_file)
        self.llm = ChatGroq(model="openai/gpt-oss-120b")

        self.agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=15,
            memory_enabled=True,
        )

    async def run_query(self, query: str, run_id: str, redis_url:str):
        """
        Run a single MCP query (used by FastAPI)
        """
        summary_prompt = """You are explaining Urban Heat Island analysis results to a general user.
        Rules:
        - Max 5-6 bullet points
        - Plain English
        - No system details
        - No IDs, Redis, tools, or model names
        - Mention counterfactuals only if present
        - you can explain why this happens, or can improve it.
        """
        response = await self.agent.run(f"{query} [run_id={run_id}] [redis_url={redis_url} [summary prompt={summary_prompt}]]")
        return response

    async def shutdown(self):
        if self.client and self.client.sessions:
            await self.client.close_all_sessions()
