from uagents import Agent, Context, Model
import os
import requests
import json
from typing import List

# === API Key ===
asi1_api_key = os.getenv("ASI1_API_KEY")

# === Sub-Agents ===
SUBAGENTS = {
    "agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5": "Resume Expert",
    "agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen": "Demand Analysis",
    "agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av": "Job Matching"
}

TAVILY_AGENT_ADDRESS = "agent1qt5uffgp0l3h9mqed8zh8vy5vs374jl2f8y0mjjvqm44axqseejqzmzx9v8"

# === Models ===
class TaskRequest(Model):
    query: str

class TaskResponse(Model):
    result: str

class WebSearchRequest(Model):
    query: str

class WebSearchResult(Model):
    title: str
    url: str
    content: str

class WebSearchResponse(Model):
    query: str
    results: List[WebSearchResult]

# === Agent Initialization ===
training_resource = Agent(name="training_resource", seed="training_resource_secret_seed")

# === Helper: ASI1 Call ===
def call_asi1(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {asi1_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "asi1-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "stream": False
    }
    try:
        response = requests.post("https://api.asi1.ai/v1/chat/completions", headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ASI1 call failed: {e}"

# === Task Handler ===
@training_resource.on_message(model=TaskRequest)
async def handle_query(ctx: Context, sender: str, msg: TaskRequest):
    ctx.logger.info(f"📩 Received training resource query: {msg.query}")
    ctx.storage.set("main_query", msg.query)
    ctx.storage.set("sender", sender)
    ctx.storage.set("subagent_results", json.dumps({}))

    try:
        await ctx.send(TAVILY_AGENT_ADDRESS, WebSearchRequest(query=msg.query))
        ctx.logger.info("🔍 Sent to Tavily Web Search Agent")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to contact Tavily: {e}")
        await fallback_response(ctx, msg.query, sender)

    # Dispatch relevant sub-agents
    q = msg.query.lower()
    if any(k in q for k in ["resume", "cv"]):
        await ctx.send(list(SUBAGENTS.keys())[0], TaskRequest(query=msg.query))
    if any(k in q for k in ["market", "demand", "trends"]):
        await ctx.send(list(SUBAGENTS.keys())[1], TaskRequest(query=msg.query))
    if any(k in q for k in ["job", "vacancy", "hiring"]):
        await ctx.send(list(SUBAGENTS.keys())[2], TaskRequest(query=msg.query))

# === Tavily Result Handler ===
@training_resource.on_message(model=WebSearchResponse)
async def handle_tavily_response(ctx: Context, sender: str, msg: WebSearchResponse):
    ctx.logger.info("🌐 Tavily response received")
    ctx.storage.set("search_summary", msg)
    await maybe_finalize(ctx)

# === Sub-agent Response Handler ===
@training_resource.on_message(model=TaskResponse)
async def handle_subagent_response(ctx: Context, sender: str, msg: TaskResponse):
    ctx.logger.info(f"📥 Sub-agent response from {sender}")
    subagent_results = json.loads(ctx.storage.get("subagent_results") or "{}")
    subagent_results[sender] = msg.result
    ctx.storage.set("subagent_results", json.dumps(subagent_results))
    await maybe_finalize(ctx)

# === Finalization ===
async def maybe_finalize(ctx: Context):
    sender = ctx.storage.get("sender")
    query = ctx.storage.get("main_query")
    search = ctx.storage.get("search_summary")
    if not sender or not query or not search:
        return

    result_list = json.loads(ctx.storage.get("subagent_results") or "{}")

    summary = ""
    for r in search.results[:3]:
        summary += f"- {r.title}: {r.content[:200]}...\nURL: {r.url}\n\n"

    subagent_contributions = ""
    if result_list:
        subagent_contributions += "\n\n🔍 Additional Insights from other Agents:\n"
        for aid, res in result_list.items():
            name = SUBAGENTS.get(aid, "Unknown")
            subagent_contributions += f"From {name}:\n{res}\n\n"
    else:
        subagent_contributions = "\n\n📝 No additional sub-agents were needed."

    asi1_prompt = f"""
You are a Training Resource and Upskilling Expert.
Given the user's query and search results, recommend 3–5 top resources (courses, platforms, certifications) that directly align with their goals.

Query: "{query}"

Search Results:
{summary}

{subagent_contributions}

Avoid asking for more input. Provide helpful, current, and actionable advice.
"""

    final_response = call_asi1(asi1_prompt)
    await ctx.send(sender, TaskResponse(result=final_response))
    ctx.logger.info("✅ Final response sent to Commander.")

# === Fallback if Tavily fails ===
async def fallback_response(ctx: Context, query: str, sender: str):
    prompt = f"""
You are a Training Resource Expert.
Without web data, provide general but helpful suggestions for 3–5 courses or certifications related to:

"{query}"
"""
    final_response = call_asi1(prompt)
    await ctx.send(sender, TaskResponse(result=final_response))
    ctx.logger.info("✅ Fallback ASI1 response sent.")

if __name__ == "__main__":
    training_resource.run()
