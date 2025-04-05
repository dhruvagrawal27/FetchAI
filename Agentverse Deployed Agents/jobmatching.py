from uagents import Agent, Context, Model
import os
import requests
from typing import List, Dict
from urllib.parse import quote_plus
import json

# ASI1 API Key
asi1_api_key = os.getenv("ASI1_API_KEY")

# Scraper + Sub-agents
SCRAPER_AGENT_ADDRESS = "agent1qwnjmzwwdq9rjs30y3qw988htrvte6lk2xaak9xg4kz0fsdz0t9ws4mwsgs"
SUBAGENTS = {
    "agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5": "Resume Expert",
    "agent1qgys89d7tr5rxxamvdhkdg80z9q99jf7sfq08kx0yftt59yjggpsk4ewgm4": "Skill Assessment",
    "agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen": "Demand Analysis",
    "agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc": "Training Resource"
}

# Keyword mapping for triggering subagents
KEYWORD_MAP = {
    "resume": "Resume Expert",
    "cv": "Resume Expert",
    "skills": "Skill Assessment",
    "qualification": "Skill Assessment",
    "trend": "Demand Analysis",
    "market": "Demand Analysis",
    "course": "Training Resource",
    "certification": "Training Resource",
    "training": "Training Resource"
}

# Agent init
job_matching = Agent(name="job_matching", seed="job_matching_secret_seed")

# Models
class TaskRequest(Model):
    query: str

class TaskResponse(Model):
    result: str

class WebsiteScraperRequest(Model):
    url: str

class WebsiteScraperResponse(Model):
    text: str

# ASI1 helper
async def call_asi1(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {asi1_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "asi1-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "stream": False
    }
    try:
        response = requests.post("https://api.asi1.ai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"ASI1 Error: {response.text}"
    except Exception as e:
        return f"ASI1 call failed: {str(e)}"

# Incoming user query
@job_matching.on_message(model=TaskRequest)
async def handle_query(ctx: Context, sender: str, msg: TaskRequest):
    ctx.logger.info(f"📩 Received query: {msg.query}")

    ctx.storage.set("query", msg.query)
    ctx.storage.set("sender", sender)
    ctx.storage.set("subagent_results", json.dumps({}))

    # Determine subagents
    triggered = set()
    for word in msg.query.lower().split():
        if word in KEYWORD_MAP:
            agent_name = KEYWORD_MAP[word]
            for address, name in SUBAGENTS.items():
                if name == agent_name:
                    triggered.add(address)

    for agent_addr in triggered:
        ctx.logger.info(f"🔄 Forwarded to sub-agent: {agent_addr}")
        await ctx.send(agent_addr, TaskRequest(query=msg.query))

    # Scraper fetch
    encoded_query = quote_plus(msg.query)
    indeed_url = f"https://in.indeed.com/jobs?q={encoded_query}&start=0"
    await ctx.send(SCRAPER_AGENT_ADDRESS, WebsiteScraperRequest(url=indeed_url))

# Handle sub-agent responses
@job_matching.on_message(model=TaskResponse)
async def collect_subagent_response(ctx: Context, sender: str, msg: TaskResponse):
    results = json.loads(ctx.storage.get("subagent_results") or "{}")
    results[sender] = msg.result
    ctx.storage.set("subagent_results", json.dumps(results))

# Handle scraper response
@job_matching.on_message(model=WebsiteScraperResponse)
async def handle_scraper(ctx: Context, sender: str, msg: WebsiteScraperResponse):
    ctx.logger.info("🔍 Scraper content received.")

    query = ctx.storage.get("query")
    sender_address = ctx.storage.get("sender")
    scraper_text = msg.text[:2000]
    subagent_results = json.loads(ctx.storage.get("subagent_results") or "{}")

    # Build annotated summary of sub-agent help
    subagent_insights = ""
    for agent_addr, content in subagent_results.items():
        name = SUBAGENTS.get(agent_addr, "Unnamed Sub-Agent")
        subagent_insights += f"\n---\n{name} Insights:\n{content.strip()}\n"

    asi1_prompt = f"""
You are a Job Matching assistant.

Based on the query and job listings, provide 3–5 most relevant job links, career suggestions, and possible training resources if needed. Do NOT ask follow-up questions.

Query: "{query}"

Scraped Job Listings:
{scraper_text}

{subagent_insights if subagent_insights else "No additional sub-agents were consulted."}
"""

    result = await call_asi1(asi1_prompt)
    await ctx.send(sender_address, TaskResponse(result=result))
    ctx.logger.info("✅ Final response sent to Commander/User.")

if __name__ == "__main__":
    job_matching.run()
