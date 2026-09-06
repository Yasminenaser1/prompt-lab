# SupplyRoom + Pitch Practice — Deploy Guide

## Folder structure
```
supplyroom/
  app.py          ← Flask backend
  requirements.txt
  render.yaml
  static/
    index.html    ← Frontend

pitchpractice/
  app.py
  requirements.txt
  render.yaml
  static/
    index.html
```

---

## Step 1 — Push to GitHub

For each app, create a separate repo:

```bash
# SupplyRoom
cd supplyroom
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/supplyroom.git
git push -u origin main

# Pitch Practice
cd ../pitchpractice
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/pitchpractice.git
git push -u origin main
```

---

## Step 2 — Deploy on Render

1. Go to https://render.com → New → **Web Service**
2. Connect your GitHub repo
3. Set these values:
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:app`
4. Click **Deploy**
5. Your app goes live at `https://your-app-name.onrender.com`

---

## Database
Both apps use **SQLite** — the `.db` file is created automatically on first run.
For production, you can swap to **PostgreSQL** on Render (free tier available).

---

## API Endpoints

### SupplyRoom
- `GET  /api/supplies` — list all supplies
- `POST /api/supplies` — add supply `{name, qty, threshold}`
- `PATCH /api/supplies/:id` — update qty/threshold
- `DELETE /api/supplies/:id` — remove supply
- `POST /api/requests` — log restock request
- `GET  /api/requests` — get request history

### Pitch Practice
- `POST /api/sessions` — save pitch text
- `GET  /api/sessions` — get saved pitches
- `POST /api/scores` — save self-score
- `GET  /api/scores` — get score history
- `GET  /api/objections?sector=Schools` — get objections
