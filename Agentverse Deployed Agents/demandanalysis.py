from uagents import Agent, Context, Model
import os
import requests
from typing import Dict, Set
import asyncio

# Use your ASI1 API Key here
asi1_api_key = os.getenv("ASI1_API_KEY")

# Sub-agent addresses
SUBAGENTS: Dict[str, str] = {
    "agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5": "Resume Expert",
    "agent1qgys89d7tr5rxxamvdhkdg80z9q99jf7sfq08kx0yftt59yjggpsk4ewgm4": "Skill Assessment",
    "agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc": "Training Resource",
    "agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av": "Job Matching"
}

# Initialize the agent
demand_analysis = Agent(name="demand_analysis", seed="demand_analysis_secret_seed")

# Models
class TaskRequest(Model):
    query: str

class TaskResponse(Model):
    result: str

class SubAgentRequest(Model):
    query: str

class SubAgentResponse(Model):
    result: str


def extract_asi1_content(response_json):
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ASI1 LLM failed to extract result: {e}"

@demand_analysis.on_message(model=TaskRequest)
async def handle_task(ctx: Context, sender: str, msg: TaskRequest):
    ctx.logger.info(f"📩 Received demand analysis query: {msg.query}")

    keyword_map = {
        "resume": "Resume Expert",
        "cv": "Resume Expert",
        "gap": "Skill Assessment",
        "upskill": "Training Resource",
        "learn": "Training Resource",
        "course": "Training Resource",
        "job": "Job Matching",
        "vacancy": "Job Matching",
        "hiring": "Job Matching"
    }

    found_agents: Set[str] = set()
    for word in msg.query.lower().split():
        if word in keyword_map:
            found_agents.add(keyword_map[word])

    subagent_responses = []
    ctx.storage.set("subagent_names", list(found_agents))

    for address, name in SUBAGENTS.items():
        if name in found_agents:
            try:
                await ctx.send(address, SubAgentRequest(query=msg.query))
                ctx.logger.info(f"🛰️ Sent query to sub-agent: {name}")
            except Exception as e:
                ctx.logger.warning(f"⚠️ Failed to send message to {name}: {e}")

    await asyncio.sleep(4)

    messages = ctx.storage.get("__messages__") or []
    for envelope in messages:
        if envelope.message and hasattr(envelope.message, 'result'):
            subagent_responses.append(envelope.message.result)

    subagent_names = ctx.storage.get("subagent_names") or []
    subagent_summary = (
        f"Additional insights were referenced from the following sub-agents: {', '.join(subagent_names)}."
        if subagent_names else
        "No additional sub-agents were needed or invoked for this demand analysis."
    )

    context_appendix = "\n---\n\nSub-Agent Context:\n" + "\n\n".join(subagent_responses) if subagent_responses else ""

    asi1_prompt = f"""
You are a Job Market Analyst specializing in demand analysis.
Analyze this user query and provide the following in a concise, quantified format:

1. **Current demand level** for the roles or skills mentioned (with estimated volume or mentions).
2. **Top 5 in-demand skills** or tools related to the query.
3. **Growth prediction** over the next 2–5 years.
4. **Relevant industries or sectors** driving the demand.
5. **Any market insights or hiring patterns** that are emerging.
6. **{subagent_summary} Always include this statement in the response.**

Query: "{msg.query}"
{context_appendix}
"""

    headers = {
        "Authorization": f"Bearer {asi1_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "asi1-mini",
        "messages": [{"role": "user", "content": asi1_prompt}],
        "temperature": 0.6,
        "stream": False
    }

    try:
        response = requests.post("https://api.asi1.ai/v1/chat/completions", headers=headers, json=data)
        result = extract_asi1_content(response.json()) if response.status_code == 200 else f"ASI1 error: {response.text}"
    except Exception as e:
        result = f"ASI1 request failed: {e}"

    await ctx.send(sender, TaskResponse(result=result))
    ctx.logger.info("✅ Final demand analysis response sent to Commander.")

if __name__ == "__main__":
    demand_analysis.run()
