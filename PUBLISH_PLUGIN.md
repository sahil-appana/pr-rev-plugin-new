# Publishing the AI PR Reviewer as a Bitbucket App and Deploying to Render

This guide walks through packaging the app as a Bitbucket Connect app, deploying the FastAPI backend to Render.com, testing the webhook, installing the app into a Bitbucket workspace, and scaling recommendations.

Prerequisites
- A Git repository with this project
- A Render.com account (or another host)
- Bitbucket Cloud account with admin rights on a workspace/repository
- API keys: `GEMINI_API_KEY` (or GROQ)

Summary of what we added
- A FastAPI server exposing: `/webhook/pr`, `/installed`, `/uninstalled` (see `bot/server.py`)
- `render.yaml` to auto-deploy on Render
- `bitbucket.json` app descriptor (update `baseUrl` before publishing)

1) Prepare the repository

- Ensure the repo has the latest changes and the FastAPI server exists at `bot/server.py`.
- Add secrets to your CI/Render settings rather than committing them.

2) Update `bitbucket.json`

- Edit the `baseUrl` field and set it to your deployed URL (e.g. `https://ai-pr-reviewer.onrender.com`).
- Confirm `lifecycle.installed` and `lifecycle.uninstalled` endpoints are correct.

3) Deploy to Render (auto-deploy on git push)

- In Render dashboard create a new Web Service.
  - Connect your Git provider and choose this repo.
  - Render will detect `render.yaml` and auto-create the service.
  - Alternatively create a new service manually and set:
    - Build command: `pip install -r requirements.txt`
    - Start command: `uvicorn bot.server:app --host 0.0.0.0 --port $PORT`

- Add environment variables in Render's dashboard (Repository/Service > Environment):
  - `GEMINI_API_KEY`, `GROQ_API_KEY`, `BITBUCKET_TOKEN`, `BITBUCKET_WORKSPACE` (optional), `ENABLE_QA_INLINE_COMMENTS=true`, `ENABLE_METRICS=true`.

4) Local testing with ngrok (optional)

- If you want to test webhooks before deploying:

  1. Start the FastAPI server locally:
     ```powershell
     python -m venv venv
     venv\Scripts\activate
     pip install -r requirements.txt
     uvicorn bot.server:app --reload --port 8000
     ```

  2. Expose it with ngrok:
     ```powershell
     ngrok http 8000
     ```

  3. Copy the public URL from ngrok (e.g. `https://abcd1234.ngrok.io`) and update `bitbucket.json`'s `baseUrl` locally for testing, or configure Bitbucket webhook to point to `https://abcd1234.ngrok.io/webhook/pr`.

5) Create/Install Bitbucket App

- If using Bitbucket Cloud Connect, go to Bitbucket settings and add an app using the `bitbucket.json` descriptor (or upload it when creating a new Connect app).
- If Bitbucket asks for a public URL during app registration, provide your Render service URL.
- Grant requested scopes: `pullrequest:read`, `pullrequest:write`, `repository:read`, `repository:write`.

6) Test the integration

- Create a dummy PR in the target repository (or use an existing PR). The webhook should trigger and POST to `/webhook/pr`.
- Verify that the app posts the QA review comment on the PR. Check Render logs or local server logs for debug messages.

7) Troubleshooting

- If you see 401/403 when fetching diffs: confirm `BITBUCKET_TOKEN` is valid and the app has the proper scopes.
- If webhooks don't arrive: check Bitbucket webhook delivery logs and your public URL.
- If the model fails to respond: check `GEMINI_API_KEY` (and network access from Render to the model API).

8) Scaling

- Start with Render's free or hobby instance for small teams. For more load:
  - Increase service plan (CPU/memory)
  - Use multiple instances behind Render's load balancer
  - Add caching layer (Redis) for shared cache across instances (current file-based cache is local to instance; to scale replace `CacheManager` with a Redis implementation)
  - Use async requests for model calls if the SDK supports it

9) Security and Best Practices

- Store secrets in Render environment, not in repo.
- Use HTTPS only.
- Limit scopes to least privilege. Consider using an installation-specific token rather than a global workspace token.
- Monitor logs and enable alerts for errors or high error rates.

10) Release Workflow

- Push changes to `main` branch. Render will auto-deploy if connected.
- Run end-to-end test: create PR -> confirm QA review posted -> confirm inline comments.

11) Next steps / Advanced

- Add authentication for incoming webhooks (JWT verification) using Bitbucket Connect JWT: verify `Authorization` header.
- Replace file-based cache with Redis to share cache across instances.
- Add metrics collection (Prometheus) and error tracking (Sentry).
