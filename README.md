# GitHub Profile Analyzer AI Agent 👤🔍

An intelligent, context-locked conversational agent that profiles any GitHub user on demand. Powered by the **Model Context Protocol (MCP)** and **Mistral AI**, this script shifts focus from individual repository management to user-centric analysis—automatically discovering a user's bio, analyzing their dominant programming stacks, and evaluating recent code metrics.

## 🌟 Capabilities

- **Automated Bio Discovery:** Automatically targets and parses the special personal profile repository (`username/username`) to extract their introduction.
- **Dynamic Chronology Correction:** Injects real-time local timestamps so the AI can audit today's live event activity stream without temporal confusion.
- **Full History Auditing:** Interrogates public repos, recent commits, and open contribution threads linked to that specific developer footprint.

---

## 🛠️ Setup Instructions

### 1. Prerequisites

Ensure you have completed the base setup from the main project guide:

- Docker Desktop is open and active.
- Your virtual environment is running (`source myenv/bin/activate`).
- Your `.env` file contains valid `MISTRAL_API_KEY` and `GITHUB_PERSONAL_ACCESS_TOKEN` values.

### 2. Create the Script

Ensure you have created the `profile_agent.py` file in your root project folder alongside your original agent assets.

---

## 💻 Usage

1. Fire up the profile analysis script inside your active terminal:

   ```bash
   python profile_agent.py
   ```

2. Enter the target GitHub username when prompted:

   ```text
   👤 Enter GitHub Username to Analyze (e.g. 'kunal031'): kunal031
   ```

3. Ask targeted questions about their development activity:
   ```text
   ❓ Question about @kunal031: What are their top programming languages?
   ❓ Question about @kunal031: Summarize what projects they worked on today.
   ```

---

## 💡 Recommended Queries to Test

- **Stack Analysis:** _"Based on their public repositories, what technologies or frameworks do they use most?"_
- **Activity Feed Audit:** _"List any commits or pull request modifications they made on today's date."_
- **Code Architecture Check:** _"Look at their 'FastAPI' repo and find where their main application routers are located."_

---

## 📁 Repository Placement

Your project workspace should now look like this:

```text
GITHUB-PROFILE_AGENT/
│
├── myenv/               # Python environment configuration files
├── .env                 # API Credentials (Protected/Hidden)
├── .gitignore           # Stops secrets from leaking into code history
├── agent.py             # Base General Repository Query Agent
├── profile_agent.py     # New Targeted Profile Analyzer Agent 🌟
└── README.md    # User profiling documentation
```
