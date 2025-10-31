#!/usr/bin/env python3
"""
PyDeployer — Local Python DevOps automation tool
This version:
 - Works completely locally
 - Handles stages: example, build, test, deploy, rollback
 - Logs everything in /logs
 - No AWS or Docker
"""

import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# === Initialize color output ===
init(autoreset=True)

# === Paths ===
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# === Logging setup ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"pydeployer_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("PyDeployer")

# === Colored console messages ===
def info(msg):
    print(Fore.CYAN + msg + Style.RESET_ALL)


def success(msg):
    print(Fore.GREEN + msg + Style.RESET_ALL)


def warn(msg):
    print(Fore.YELLOW + msg + Style.RESET_ALL)


def error(msg):
    print(Fore.RED + msg + Style.RESET_ALL)


# === Load configuration ===
def load_config():
    path = BASE_DIR / "pipeline.yml"
    if not path.exists():
        warn("⚠️ pipeline.yml not found, continuing with defaults.")
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


# === Log cleanup (keep last 10) ===
def clean_old_logs():
    logs = sorted(LOG_DIR.glob("pydeployer_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_log in logs[10:]:  # keep 10 latest
        old_log.unlink(missing_ok=True)
        logger.info(f"🗑️ Deleted old log: {old_log.name}")


# === Example stage ===
def run_example_stage():
    info("=== Running Example Stage ===")
    try:
        logger.info("Performing example operation...")
        print("Simulating a local deployment step...")
        success("✅ Example stage completed successfully.")
        logger.info("Example stage finished successfully.")
        return True
    except Exception as e:
        error(f"❌ Example stage failed: {e}")
        logger.error(f"Example stage failed: {e}")
        return False


# === Build stage ===
def build(config):
    info("=== Starting BUILD stage ===")
    logger.info("Running local build simulation...")
    print("Building application locally...")
    success("✅ Build completed successfully.")
    logger.info("Build stage finished successfully.")


# === Test stage ===
def test(config):
    info("=== Starting TEST stage ===")
    logger.info("Running local test simulation...")
    print("Running unit tests...")
    success("✅ All tests passed.")
    logger.info("Test stage finished successfully.")


# === Deploy stage ===
def deploy(config):
    info("=== Starting DEPLOY stage ===")
    logger.info("Simulating local deployment...")
    print("Deploying application locally...")
    success("✅ Deploy completed successfully.")
    logger.info("Deploy stage finished successfully.")


# === Rollback stage ===
def rollback(config):
    warn("=== Starting ROLLBACK stage ===")
    logger.info("Simulating rollback procedure...")
    print("Rolling back to previous version...")
    success("✅ Rollback completed.")
    logger.info("Rollback stage finished successfully.")


# === Main entrypoint ===
def run_stage(stage_name: str):
    config = load_config()
    clean_old_logs()

    stages = {
        "example": run_example_stage,
        "build": build,
        "test": test,
        "deploy": deploy,
        "rollback": rollback,
    }

    if stage_name in stages:
        stages[stage_name](config)
    else:
        warn(f"⚠️ Stage '{stage_name}' not implemented yet.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyDeployer Local CLI")
    parser.add_argument(
        "stage",
        choices=["example", "build", "test", "deploy", "rollback"],
        help="Specify which stage to run",
    )
    args = parser.parse_args()

    run_stage(args.stage)
