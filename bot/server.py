from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from typing import Optional

from bot.core.logger import ReviewLogger
from bot.core.reviewer_engine import ReviewerEngine
from bot.core.bitbucket_api import BitbucketAPI
from bot.core.qa_issue_extractor import QAIssueExtractor
from bot.core.qa_formatter import QAFormatter
from bot.config import Config

app = FastAPI(title="AI PR Reviewer - QA Mode Webhook")
logger = ReviewLogger.setup(verbose=Config.VERBOSE_LOGGING)


def _make_api_with_context(workspace: str, repo_slug: str, pr_id: str, token: Optional[str] = None) -> BitbucketAPI:
    api = BitbucketAPI()
    # override context from webhook payload
    api.workspace = workspace
    api.repo_slug = repo_slug
    api.pr_id = str(pr_id)
    api.base = f"{Config.BITBUCKET_BASE_URL}/repositories/{workspace}/{repo_slug}"
    # use provided token or env token
    access_token = token or Config.BITBUCKET_TOKEN
    api.access_token = access_token
    api.headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    return api


@app.post('/installed')
async def installed(request: Request):
    payload = await request.json()
    logger.info(f"App installed: {payload.get('clientKey') or payload.get('repository')}")
    return JSONResponse({"status": "ok"})


@app.post('/uninstalled')
async def uninstalled(request: Request):
    payload = await request.json()
    logger.info(f"App uninstalled: {payload.get('clientKey') or payload.get('repository')}")
    return JSONResponse({"status": "ok"})


@app.post('/webhook/pr')
async def webhook_pr(request: Request, x_event_key: Optional[str] = Header(None)):
    """Handle Bitbucket PR webhooks (pullrequest:created, updated, reopened)

    This function is intentionally small and delegates work to helpers.
    """
    payload = await _parse_json_request(request)
    repo, pr = _extract_repo_pr(payload)
    workspace, repo_slug, pr_id = _extract_repo_info(repo, pr)
    logger.info(f"Received PR webhook: {workspace}/{repo_slug} PR#{pr_id} event={x_event_key}")

    api = _make_api_with_context(workspace, repo_slug, pr_id)
    diff = await _resolve_diff_from_payload(api, payload)

    review_text = _run_qa_review(payload, pr_id, diff)

    posted = api.post_comment(review_text)
    _post_inline_comments(api, review_text)

    return JSONResponse({"status": "review_posted" if posted else "review_generated"})


@app.get('/health')
async def health():
    return JSONResponse({"status": "ok", "service": "ai-pr-reviewer", "qa_mode": Config.QA_MODE})


async def _parse_json_request(request: Request) -> dict:
    try:
        return await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")


def _extract_repo_pr(payload: dict):
    repo = payload.get('repository') or payload.get('pullrequest', {}).get('destination', {}).get('repository')
    pr = payload.get('pullrequest') or payload.get('pullrequest')
    if not repo or not pr:
        logger.error('Webhook payload missing repository or pullrequest data')
        raise HTTPException(status_code=400, detail='Missing repository or pullrequest')
    return repo, pr


def _extract_repo_info(repo: dict, pr: dict):
    workspace = repo.get('workspace', {}).get('slug') or repo.get('owner', {}).get('username') or (repo.get('full_name', '').split('/')[0] if repo.get('full_name') else None)
    repo_slug = repo.get('slug') or repo.get('name') or (repo.get('full_name', '').split('/')[1] if repo.get('full_name') else None)
    pr_id = pr.get('id') or pr.get('iid')
    if not (workspace and repo_slug and pr_id):
        logger.error('Could not determine workspace, repo_slug or pr_id from payload')
        raise HTTPException(status_code=400, detail='Incomplete repo/pr info')
    return workspace, repo_slug, pr_id


def _resolve_diff_from_payload(api: BitbucketAPI, payload: dict) -> str:
    if 'pullrequest' in payload and payload['pullrequest'].get('links', {}).get('diff'):
        try:
            return api.get_pr_diff()
        except Exception as e:
            logger.warning(f"Failed to fetch diff via API: {e}")
            return ''
    return payload.get('diff') or payload.get('pullrequest', {}).get('description', '')


def _run_qa_review(payload: dict, pr_id, diff: str) -> str:
    engine = ReviewerEngine()
    title = payload.get('pullrequest', {}).get('title', f'PR {pr_id}')
    desc = payload.get('pullrequest', {}).get('description', '')
    return engine.generate_review(title, desc, diff)


def _post_inline_comments(api: BitbucketAPI, review_text: str) -> None:
    extractor = QAIssueExtractor()
    issues = extractor.extract_issues(review_text)
    actionable = extractor.extract_high_medium_issues(issues)
    if actionable and Config.ENABLE_QA_INLINE_COMMENTS:
        grouped = extractor.group_issues_by_location(actionable)
        for (file_path, line_num), issues_bucket in grouped.items():
            for issue in issues_bucket:
                comment = QAFormatter.format_inline_comment(issue)
                api.post_inline_comment(file_path, line_num, comment)
