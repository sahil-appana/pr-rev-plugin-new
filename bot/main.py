import os
import sys
from bot.config import Config
from bot.core.logger import ReviewLogger
from bot.core.bitbucket_api import BitbucketAPI
from bot.core.reviewer_engine import ReviewerEngine
from bot.core.qa_issue_extractor import QAIssueExtractor
from bot.core.qa_formatter import QAFormatter

def _post_qa_inline_comments(api: BitbucketAPI, review: str) -> None:
    """Extract and post QA inline comments"""
    logger = ReviewLogger.get()
    
    if not (Config.QA_MODE and Config.ENABLE_QA_INLINE_COMMENTS):
        return
    
    logger.info("Extracting QA issues for inline comments...")
    extractor = QAIssueExtractor()
    qa_issues = extractor.extract_issues(review)
    high_medium_issues = extractor.extract_high_medium_issues(qa_issues)
    
    if not high_medium_issues:
        logger.debug("No HIGH/MEDIUM issues with file locations for inline comments")
        return
    
    logger.info(f"Posting {len(high_medium_issues)} inline QA comments...")
    grouped = extractor.group_issues_by_location(high_medium_issues)
    
    for (file_path, line_num), issues in grouped.items():
        for issue in issues:
            comment = QAFormatter.format_inline_comment(issue)
            api.post_inline_comment(file_path, line_num, comment)

def run():
    """Main entry point for PR review"""
    # Initialize logging
    ReviewLogger.setup(verbose=Config.VERBOSE_LOGGING)
    logger = ReviewLogger.get()
    
    # Validate configuration
    config_error = Config.validate()
    if config_error:
        logger.error(f"Configuration error: {config_error}")
        sys.exit(1)
    
    logger.info("Starting AI PR Reviewer")
    logger.debug(f"Config: QA_MODE=ALWAYS_ACTIVE, DRY_RUN={Config.DRY_RUN}, ENABLE_METRICS={Config.ENABLE_METRICS}")
    
    try:
        # Get Bitbucket API and ReviewerEngine
        api = BitbucketAPI()
        engine = ReviewerEngine()
        
        # Fetch PR metadata and diff
        logger.info("Fetching PR metadata and diff...")
        title, desc = api.get_pr_metadata()
        diff = api.get_pr_diff()
        
        if not diff:
            logger.error("Failed to fetch PR diff")
            sys.exit(1)
        
        # Generate review
        logger.info("Generating review...")
        review = engine.generate_review(title, desc, diff)
        
        # Post comment
        logger.info("Posting review comment...")
        success = api.post_comment(review)
        
        if success:
            logger.info("Review completed successfully")
        else:
            logger.warning("Review generated but failed to post")
            sys.exit(1)
    except Exception as e:
        # Extract and post inline QA comments
        _post_qa_inline_comments(api, review)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    run()
