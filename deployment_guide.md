# Deployment Guide: Owntrail AI Support Engine

This guide walks you through deploying the **FastAPI Backend (Render)** and **React Frontend (Vercel)** using your specific keys.

---

## Part 1: Backend Deployment (Render)

1.  **Push your code to GitHub**.
2.  **Sign up/Login to [Render.com](https://render.com)**.
3.  Click **"New +"** -> **"Web Service"**.
4.  Connect your GitHub repository.
5.  **Configure**:
    *   **Name**: `owntrail-api`
    *   **Root Directory**: `ai_support_engine`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `python src/main.py`

6.  **Environment Variables (Key-Value Pairs)**:
    Add these in the "Environment" tab:
    *   `OPENAI_API_KEY`: `sk-proj-dkD6gpNL...` (Your full key)
    *   `inferenceapi`: `YOUR_HUGGINGFACE_TOKEN`
    *   `FIREBASE_KEY_PATH`: `/etc/secrets/firebase_key.json`  <-- **IMPORTANT**

7.  **Secret Files (The JSON Key)**:
    *   Scroll down to **"Secret Files"** (This is separate from Env Vars).
    *   Click "Add Secret File".
    *   **Filename**: `firebase_key.json`
    *   **Content**: Open your local `ai_support_engine/ticketsupportresolution-firebase-adminsdk-fbsvc-1beb54c348.json` file, copy all the requested JSON content, and paste it here.
    *   *Note: This magically creates the file at `/etc/secrets/firebase_key.json` on the server.*

8.  **Click "Create Web Service"**.
    *   Wait for it to go live. Copy the URL (e.g., `https://owntrail-api.onrender.com`).

---

## Part 2: Frontend Deployment (Vercel)

1.  **Sign up/Login to [Vercel.com](https://vercel.com)**.
2.  Click **"Add New..."** -> **"Project"**.
3.  Import your GitHub repository.
4.  **Configure**:
    *   **Root Directory**: Select `frontend`.
    *   **Framework Preset**: Vite

5.  **Environment Variables**:
    Copy-paste these exactly:
    *   `VITE_FIREBASE_API_KEY`: `AIzaSyB1TWUQnkmxbfWGgrRKFP4v6SlLDQtA05w`
    *   `VITE_FIREBASE_AUTH_DOMAIN`: `ticketsupportresolution.firebaseapp.com`
    *   `VITE_FIREBASE_PROJECT_ID`: `ticketsupportresolution`
    *   `VITE_FIREBASE_STORAGE_BUCKET`: `ticketsupportresolution.firebasestorage.app`
    *   `VITE_FIREBASE_MESSAGING_SENDER_ID`: `180905450500`
    *   `VITE_FIREBASE_APP_ID`: `1:180905450500:web:27ab6a80c61bc10596e951`
    *   `VITE_API_BASE_URL`: `https://your-render-backend-url.onrender.com` (**Update this with your actual Render URL from Part 1**)

6.  **Click "Deploy"**.

---

## Part 3: Final Integration Check
1.  Open your Vercel URL.
2.  If the backend URL is set correctly, everything should work!
3.  Debug Tip: If tickets don't load, check the Browser Console (F12) to see if it's trying to hit `localhost` or the `onrender.com` URL.
