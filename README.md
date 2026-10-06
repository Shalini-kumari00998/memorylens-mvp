# MemoryLens — AI-Native Photo Retrieval MVP

Conversational AI assistant that helps users find vaguely-remembered photos in Google Photos.

## Deploy on Render

1. Fork / push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Apply**
5. In the **Environment** tab, set `GEMINI_API_KEY` to your Gemini API key
6. Click **Deploy** → get your public URL

## Run locally

```bash
pip install -r requirements.txt
# Demo mode (no key needed):
python app.py
# With live Gemini:
GEMINI_API_KEY=your_key python app.py
```

Open http://localhost:5000
