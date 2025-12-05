# Local simulation script - runs reviewer against a local diff file
import os
import sys
from bot.config import Config
from bot.core.logger import ReviewLogger
from bot.core.reviewer_engine import ReviewerEngine
from bot.core.metrics_analyzer import MetricsAnalyzer

def load_diff(path):
    """Load diff from file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    # Setup logging
    ReviewLogger.setup(verbose=Config.VERBOSE_LOGGING)
    logger = ReviewLogger.get()
    
    if len(sys.argv) < 2:
        print("Usage: python simulate_review.py <diff_file>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if not os.path.exists(path):
        logger.error(f"Diff file not found: {path}")
        sys.exit(1)
    
    logger.info(f"Loading diff from {path}")
    diff = load_diff(path)
    
    logger.info("QA Mode: ALWAYS ACTIVE")
    
    # Analyze metrics
    if Config.ENABLE_METRICS:
        logger.info("Analyzing PR metrics...")
        metrics = MetricsAnalyzer.analyze(diff)
        print("\n=== PR METRICS ===")
        for key, value in metrics.to_dict().items():
            print(f"{key}: {value}")
    
    # Generate review
    engine = ReviewerEngine()
    title = "Local simulation"
    desc = "This is a simulated PR for testing."
    
    logger.info("Generating review...")
    review = engine.generate_review(title, desc, diff)
    
    print("\n=== GENERATED REVIEW ===")
    print(review)
    
    logger.info("Review complete")

if __name__ == '__main__':
    main()
