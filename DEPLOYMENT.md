# Deploying the Flask POC

This guide shows two easy ways to host your Flask + OpenCV app, and how to wire the frontend button.

## 1) Railway (recommended)
- Repo: connect GitHub repo to Railway
- Service: create a new **Web Service** from this repo
- Build: auto
- Start command: provided by `Procfile` (Railway uses it automatically)
- Env vars:
  - `PORT` (Railway sets it automatically)
  - `FLASK_SECRET_KEY`: a random secret
  - `FRONTEND_ORIGINS`: `http://localhost:8080,https://<your-vercel-domain>`
- Health: GET `/healthz`

## 2) Render
- Create a **Web Service** from repo
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn server.app:app --timeout 180 --workers 1 --threads 2 --preload -b 0.0.0.0:$PORT`
- Env vars: same as above

## 3) Docker-based (Fly.io / Cloud Run)
- Uses the provided `Dockerfile`
- Ensure port 8080 and `PORT` env set by platform

## Frontend wiring (Vercel)
- In Vercel Project Settings → Environment Variables:
  - `VITE_POC_URL` = `https://your-flask-host.example.com`
- Redeploy; the hero button opens the hosted POC.

## Notes
- The app accepts two images and writes a result to a temp directory; treat filesystem as ephemeral in production.
- For persistence, push results to object storage (S3, GCS, etc.).
- Increase memory if OpenCV fails on large images.
