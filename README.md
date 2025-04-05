# CareerSaathi: AI-Driven Career Guidance for Job Seekers

**CareerSaathi** is an AI-powered ecosystem built using the Fetch.ai **uAgents framework** and powered exclusively by the **ASI1 LLM API**. It assists job seekers with personalized career guidance, resume evaluation, skill gap analysis, training resource recommendations, and real-time job matching — all performed by intelligent autonomous agents.

![tag : innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

---

## 🚀 Key Features

- **Resume Expert**: Evaluates and refines user resumes. Collaborates with Skill and Demand agents for deeper insights.
- **Skill Assessment**: Provides structured evaluation, identifies gaps, and suggests actionable improvements. Communicates with Resume, Training, Demand, and Job Matching agents.
- **Demand Analysis**: Analyzes job market trends and future growth. Integrates with financial sentiment APIs and informs other agents like Resume and Training.
- **Training Resource**: Recommends personalized courses using Tavily Web Search and scraper tools. Can collaborate with Demand Analysis for more relevant resources.
- **Job Matching**: Matches users to recent job listings scraped from Indeed. Integrates Resume, Skill, and Training agent outputs to enhance match accuracy.

---

## 🧠 How It Works

- Powered entirely by **ASI1 LLM** for all reasoning and text generation.
- Agents are deployed using the **uAgents framework** on **Fetch.ai** and interact dynamically through the **Agentverse**.
- Sub-agents share context and results with each other to enrich responses.
- Scraping and web-search are used where needed (e.g., job listings, courses, market news).

---

## 🧩 System Components

| Agent            | Description                                                                      | Agentverse Link |
|------------------|----------------------------------------------------------------------------------|------------------|
| **Commander**    | Central agent that routes each user query to the most suitable sub-agent         | [🔗 Commander](https://agentverse.ai/agents/details/agent1qtjjk3xfvel6qkqk48n2he4kwqmytwcc6tplvszvwty9qp38nfs4w3r3xme/profile) |
| **Resume Expert**| Analyzes resumes and optionally calls Skill or Demand agents                     | [🔗 Resume Expert](https://agentverse.ai/agents/details/agent1qvpk7cwgjfdtzfsxv092gcdu0sdsu43z6p0z8nrfckxmcmzd532dgxuy0x5/profile) |
| **Skill Assessment**| Evaluates user skills, calls other agents when needed                         | [🔗 Skill Assessment](https://agentverse.ai/agents/details/agent1qgys89d7tr5rxxamvdhkdg80z9q99jf7sfq08kx0yftt59yjggpsk4ewgm4/profile) |
| **Demand Analysis**| Uses ASI1 + Financial Sentiment to generate demand reports                     | [🔗 Demand Analysis](https://agentverse.ai/agents/details/agent1qfvyd3y9qf9cmsl2waatsdchumu8gjj2fl6ynuzy0mlqcjwpge6ekp74qen/profile) |
| **Training Resource**| Uses Tavily and scraper to recommend learning resources                      | [🔗 Training Resource](https://agentverse.ai/agents/details/agent1qvfed9rmxdz4j488gqvannjs6fatpl3u0ehk2kelez6pz8tr2u8nyxjg5kc/profile) |
| **Job Matching** | Finds relevant jobs, and uses Resume + Skill + Training for profile-based match  | [🔗 Job Matching](https://agentverse.ai/agents/details/agent1qv4xn6kxtylzyvf5zc4ywx4qcq2g3q6cp2mpvz8twkwmtnm27gl6xp9x7av/profile) |

---

## ⚙️ Installation & Setup

```bash
git clone https://github.com/dhruvagrawal27/FetchAI.git
cd FetchAI
pip install -r requirements.txt
python testagent.py
```

---

## 💡 Usage

1. Start the system by running `testagent.py`.
2. Type a career query such as:
   ```
   "Find me jobs in Bangalore for backend developer. Is my resume strong enough? Suggest courses to improve."
   ```
3. The system will:
   - Analyze and extract the core context using ASI1
   - Dynamically dispatch the query to the best agent
   - Sub-agents may collaborate and enrich the response
   - Return a comprehensive answer with job links, resume suggestions, skill gaps, and learning paths

---

## ✅ What's New?

- ✅ Full transition from OpenAI to **ASI1**
- ✅ **Sub-agent collaboration** fully implemented (e.g., Resume Expert gets help from Skill Agent)
- ✅ **Tavily Web Search** and **scraper integration** for real-time external data
- ✅ **Dynamic response generation** based on actual agent communication

---

## 🎯 Impact

- Makes career guidance **AI-native** and **agent-driven**.
- Helps job seekers in India and beyond get **personalized, real-time** advice.
- Bridges job market signals, skills gaps, and educational resources into one platform.
