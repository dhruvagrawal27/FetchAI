from uagents import Agent, Context, Model
import os
import requests
import json
from typing import Dict

# ASI1 API Key
asi1_api_key = os.getenv("ASI1_API_KEY")

# Agent Initialization
skill_assessment = Agent(name="skill_assessment", seed="skill_assessment_secret_seed")

# Sub-agents
SUBAGENTS = {
    "agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5": "Resume Expert",
    "agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen": "Demand Analysis",
    "agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc": "Training Resource",
    "agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av": "Job Matching"
}

# Models
class TaskRequest(Model):
    query: str

class TaskResponse(Model):
    result: str

# Storage keys
QUERY_KEY = "skill_query"
SENDER_KEY = "skill_sender"
RESPONSES_KEY = "skill_responses"
PENDING_KEY = "pending_agents"

# Helper to query ASI1
async def call_asi1(prompt: str) -> str:
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
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else f"ASI1 error: {response.text}"
    except Exception as e:
        return f"ASI1 call failed: {str(e)}"

# Incoming user query
@skill_assessment.on_message(model=TaskRequest)
async def handle_skill_query(ctx: Context, sender: str, msg: TaskRequest):
    ctx.logger.info(f"📩 Skill Assessment Query Received: {msg.query}")

    ctx.storage.set(QUERY_KEY, msg.query)
    ctx.storage.set(SENDER_KEY, sender)
    ctx.storage.set(RESPONSES_KEY, json.dumps({}))

    relevant_agents = []
    keywords = msg.query.lower()
    if any(k in keywords for k in ["resume", "cv"]):
        relevant_agents.append("agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5")
    if any(k in keywords for k in ["trend", "demand", "market"]):
        relevant_agents.append("agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen")
    if any(k in keywords for k in ["course", "training", "certification"]):
        relevant_agents.append("agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc")
    if any(k in keywords for k in ["job", "apply", "vacancy"]):
        relevant_agents.append("agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av")

    ctx.storage.set(PENDING_KEY, json.dumps(relevant_agents))

    for agent in relevant_agents:
        await ctx.send(agent, TaskRequest(query=msg.query))
        ctx.logger.info(f"📤 Sent to sub-agent: {agent}")

    if not relevant_agents:
        await generate_final_response(ctx)

# Handle sub-agent responses
@skill_assessment.on_message(model=TaskResponse)
async def handle_subagent_response(ctx: Context, sender: str, msg: TaskResponse):
    responses = json.loads(ctx.storage.get(RESPONSES_KEY) or "{}")
    responses[sender] = msg.result
    ctx.storage.set(RESPONSES_KEY, json.dumps(responses))

    pending = json.loads(ctx.storage.get(PENDING_KEY) or "[]")
    if sender in pending:
        pending.remove(sender)
        ctx.storage.set(PENDING_KEY, json.dumps(pending))

    if not pending:
        await generate_final_response(ctx)

# Combine and respond
async def generate_final_response(ctx: Context):
    query = ctx.storage.get(QUERY_KEY)
    sender_address = ctx.storage.get(SENDER_KEY)
    responses = json.loads(ctx.storage.get(RESPONSES_KEY) or "{}")

    if responses:
        subagent_summary = "Additional sub-agent insights were included:\n"
        for k, v in responses.items():
            name = SUBAGENTS.get(k, k[-6:])
            subagent_summary += f"\n🔹 {name}:\n{v}\n"
    else:
        subagent_summary = "No sub-agent insights were required based on the query.\n"

    prompt = f"""
You are a Skill Assessment expert.
Evaluate the user's query, identify current strengths and weaknesses, benchmark skills against industry needs, and recommend improvements.
Provide: structured evaluation, gap identification, actionable advice.

Query: "{query}"

{subagent_summary}
"""

    final_result = await call_asi1(prompt)
    await ctx.send(sender_address, TaskResponse(result=final_result))
    ctx.logger.info("✅ Final skill assessment response sent.")

if __name__ == "__main__":
    skill_assessment.run()
