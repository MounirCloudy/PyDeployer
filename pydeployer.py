#!/usr/bin/env python3
"""
PyDeployer — Local Python DevOps automation tool

This version:
 - Works completely locally
 - Handles stages: clone, build, test, deploy, rollback
 - Interacts with a real GitHub repository via Git CLI
 - Logs everything in /logs
 - Uses only standard Python modules (plus colorama, yaml)
"""

import logging
import sys
import yaml
import subprocess
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
def info(msg): print(Fore.CYAN + msg + Style.RESET_ALL)
def success(msg): print(Fore.GREEN + msg + Style.RESET_ALL)
def warn(msg): print(Fore.YELLOW + msg + Style.RESET_ALL)
def error(msg): print(Fore.RED + msg + Style.RESET_ALL)

# === Utility to run commands ===
def run_cmd(cmd, cwd=None):
    """Run a system command and log output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.info(result.stdout.strip())
        if result.stderr:
            logger.warning(result.stderr.strip())
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)
        error(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(1)

# === Load configuration ===
def load_config():
    path = BASE_DIR / "pipeline.yml"
    if not path.exists():
        warn("⚠️ pipeline.yml not found, continuing with defaults.")
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

# === Clean old logs (keep last 10) ===
def clean_old_logs():
    logs = sorted(LOG_DIR.glob("pydeployer_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_log in logs[10:]:
        old_log.unlink(missing_ok=True)
        logger.info(f"🗑️ Deleted old log: {old_log.name}")

# === CLONE STAGE ===
def clone_repo(config):
    info("=== Starting CLONE stage ===")
    repo_url = config.get("repo", {}).get("url")
    target_dir = config.get("repo", {}).get("target", "target_repo")

    if not repo_url:
        error("❌ No repository URL specified in pipeline.yml under 'repo.url'")
        sys.exit(1)

    target_path = BASE_DIR / target_dir

    if target_path.exists():
        info(f"📦 Repository already exists at {target_path}. Pulling latest changes...")
        run_cmd(["git", "pull"], cwd=target_path)
    else:
        info(f"📥 Cloning repository from {repo_url} into {target_dir}...")
        run_cmd(["git", "clone", repo_url, target_dir])
    
    success("✅ Repository ready.")
    logger.info(f"Clone stage finished successfully for {repo_url}")

# === BUILD STAGE ===
def build(config):
    info("=== Starting BUILD stage ===")
    repo_dir = BASE_DIR / config.get("repo", {}).get("target", "target_repo")
    if not repo_dir.exists():
        error("❌ Repository not cloned yet. Run 'clone' first.")
        sys.exit(1)

    run_cmd(["git", "add", "."], cwd=repo_dir)
    commit_msg = f"Build commit at {datetime.now().isoformat()}"
    run_cmd(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    success("✅ Build (commit) completed successfully.")
    logger.info("Build stage finished successfully.")

# === TEST STAGE ===
def test(config):
    info("=== Starting TEST stage ===")
    repo_dir = BASE_DIR / config.get("repo", {}).get("target", "target_repo")
    test_command = config.get("test", {}).get("command", "pytest -v")

    info(f"🧪 Running tests using: {test_command}")
    try:
        run_cmd(test_command.split(), cwd=repo_dir)
        success("✅ All tests passed.")
    except Exception as e:
        error(f"❌ Tests failed: {e}")
        sys.exit(1)

# === DEPLOY STAGE ===
def deploy(config):
    info("=== Starting DEPLOY stage ===")
    repo_dir = BASE_DIR / config.get("repo", {}).get("target", "target_repo")
    branch = config.get("deploy", {}).get("branch", "main")

    run_cmd(["git", "pull", "origin", branch, "--rebase"], cwd=repo_dir)
    run_cmd(["git", "push", "origin", branch], cwd=repo_dir)
    success(f"✅ Code deployed to branch '{branch}'.")
    logger.info("Deploy stage finished successfully.")

# === ROLLBACK STAGE ===
def rollback(config):
    warn("=== Starting ROLLBACK stage ===")
    repo_dir = BASE_DIR / config.get("repo", {}).get("target", "target_repo")

    try:
        run_cmd(["git", "revert", "--no-edit", "HEAD"], cwd=repo_dir)
        run_cmd(["git", "push", "origin", "main"], cwd=repo_dir)
        success("✅ Rollback completed and pushed.")
        logger.info("Rollback stage finished successfully.")
    except Exception as e:
        error(f"❌ Rollback failed: {e}")
        sys.exit(1)

# === MAIN ENTRYPOINT ===
def run_stage(stage_name: str):
    config = load_config()
    clean_old_logs()

    stages = {
        "clone": clone_repo,
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

    parser = argparse.ArgumentParser(description="PyDeployer Local GitHub Automation CLI")
    parser.add_argument(
        "stage",
        choices=["clone", "build", "test", "deploy", "rollback"],
        help="Specify which stage to run",
    )
    args = parser.parse_args()
    run_stage(args.stage)
