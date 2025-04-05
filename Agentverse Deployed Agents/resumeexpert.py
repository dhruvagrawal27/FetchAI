from uagents import Agent, Context, Model
import os
import requests
import json

# ASI1 API Key
asi1_api_key = os.getenv("ASI1_API_KEY")

# Sub-agent registry
SUBAGENTS = {
    "agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen": "Demand Analysis",
    "agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc": "Training Resource",
    "agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av": "Job Matching"
}

# Models
class TaskRequest(Model):
    query: str

class TaskResponse(Model):
    result: str

# Initialize agent
resume_expert = Agent(name="resume_expert", seed="resume_expert_secret_seed")

# Helper to call ASI1
def call_asi1(prompt):
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
        res = requests.post("https://api.asi1.ai/v1/chat/completions", headers=headers, json=data)
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ASI1 LLM failed: {e}"

# Resume Agent Logic
@resume_expert.on_message(model=TaskRequest)
async def handle_query(ctx: Context, sender: str, msg: TaskRequest):
    ctx.logger.info(f"📩 Resume Expert received query: {msg.query}")

    ctx.storage.set("main_query", msg.query)
    ctx.storage.set("sender", sender)
    ctx.storage.set("subagent_results", json.dumps({}))

    # Forward to relevant sub-agents based on keywords
    query_lower = msg.query.lower()
    if any(w in query_lower for w in ["trend", "demand", "industry"]):
        await ctx.send(list(SUBAGENTS.keys())[0], TaskRequest(query=msg.query))
        ctx.logger.info(f"🔄 Forwarded to sub-agent: {list(SUBAGENTS.keys())[0]}")
    if any(w in query_lower for w in ["course", "certification", "learning"]):
        await ctx.send(list(SUBAGENTS.keys())[1], TaskRequest(query=msg.query))
        ctx.logger.info(f"🔄 Forwarded to sub-agent: {list(SUBAGENTS.keys())[1]}")
    if any(w in query_lower for w in ["job", "apply", "vacancy", "hiring"]):
        await ctx.send(list(SUBAGENTS.keys())[2], TaskRequest(query=msg.query))
        ctx.logger.info(f"🔄 Forwarded to sub-agent: {list(SUBAGENTS.keys())[2]}")

    # Proceed to ASI1 immediately for Resume analysis
    asi1_prompt = f"""
You are a Resume Review Expert. Given the following user resume text or description, identify:
- Key strengths
- Weak areas
- Specific improvement suggestions

Avoid vague responses. Focus on impact, relevance, and actionable improvements.

Resume Content:
\"\"\"{msg.query}\"\"\"

Also, check if any sub-agent insights are available from Demand Analysis, Training Resource, or Job Matching. Include their value in the final response under a section: "🔍 Additional Agent Insights".
"""
    response = call_asi1(asi1_prompt)
    ctx.storage.set("base_response", response)

    await maybe_finalize(ctx)

# Response handler for sub-agents
@resume_expert.on_message(model=TaskResponse)
async def handle_subagent_response(ctx: Context, sender: str, msg: TaskResponse):
    ctx.logger.info(f"📥 Sub-agent response received from {sender}")
    subagent_results = json.loads(ctx.storage.get("subagent_results") or "{}")
    subagent_results[sender] = msg.result
    ctx.storage.set("subagent_results", json.dumps(subagent_results))

    await maybe_finalize(ctx)

# Conditional response dispatch
async def maybe_finalize(ctx: Context):
    # Ensure both ASI1 and sub-agents have replied
    base_response = ctx.storage.get("base_response")
    if not base_response:
        return

    subagents_output = json.loads(ctx.storage.get("subagent_results") or "{}")
    subagent_notes = ""
    if subagents_output:
        subagent_notes = "\n\n🔍 Additional Agent Insights:\n"
        for agent, content in subagents_output.items():
            subagent_notes += f"From {SUBAGENTS.get(agent, 'Unknown')}:\n{content.strip()}\n\n"
    else:
        subagent_notes = "\n\n📝 No additional sub-agents were needed for this resume evaluation."

    full_reply = base_response.strip() + subagent_notes
    await ctx.send(ctx.storage.get("sender"), TaskResponse(result=full_reply))
    ctx.logger.info("✅ Final Resume Expert response sent to Commander.")

# Run agent
if __name__ == "__main__":
    resume_expert.run()
