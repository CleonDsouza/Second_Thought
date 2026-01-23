# Second Thought

A decision-analysis web app that uses AI to evaluate emotional, logical,
and intellectual reasoning, with post-decision reflection.

## Features
- AI-based reasoning analysis
- Bias detection
- Reflection after outcomes
- Clean modern UI

## Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Auth:** Firebase Authentication
- **AI:** Ollama (local LLM)

## Team Members
- Cleon – Backend
- Aditya – Frontend Logic
- Tanish – Frontend
- Sujal – Backend & Testing

## How to Run
```bash
pip install -r requirements.txt
python app.py# Second_Thought

🤖 Local AI Setup (Ollama)

Second Thought runs 100% locally using Ollama.
You must install Ollama and download a model before running the app.

1️⃣ Install Ollama

Download Ollama for your operating system:

👉 https://ollama.com/download

After installation, verify it works:

ollama --version


Ollama runs a local server on:

http://localhost:11434


⚠️ Keep Ollama running while using the app.

2️⃣ Choose Your AI Model

Second Thought supports two local models.
You only need to install one.

🟢 Option A: Llama 3.2 (3B) — Recommended

Best balance of speed, reasoning quality, and low RAM usage.

ollama pull llama3.2:3b


✔ Fast on most laptops
✔ Lower memory usage
✔ Best default choice

🔵 Option B: Mistral

More expressive language, but slower and uses more memory.

ollama pull mistral


✔ Better writing style
✖ Slower on low-end machines

3️⃣ Select the Model in the App

Open app1.py and set the model name:

MODEL_NAME = "llama3.2:3b"
# or
MODEL_NAME = "mistral"


Then make sure your Ollama request uses it:

"model": MODEL_NAME,


Restart the app after changing the model.

4️⃣ Test Ollama Manually (Optional)

To confirm everything works:

ollama run llama3.2:3b


or

ollama run mistral


If the model responds, you’re good to go ✅