#!/usr/bin/env python3
"""
PyDeployer — Python DevOps automation tool
"""

import subprocess, logging, sys, yaml
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# === Initialize colorama for colors in IPython ===
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
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("PyDeployer")

# === Helper functions for colors ===
def info(msg): print(Fore.CYAN + msg + Style.RESET_ALL)
def success(msg): print(Fore.GREEN + msg + Style.RESET_ALL)
def warn(msg): print(Fore.YELLOW + msg + Style.RESET_ALL)
def error(msg): print(Fore.RED + msg + Style.RESET_ALL)

# === Config loader ===
def load_config():
    path = BASE_DIR / "pipeline.yml"
    if not path.exists():
        error("❌ pipeline.yml not found!")
        sys.exit(1)
    with open(path, "r") as f:
        return yaml.safe_load(f)

# === BUILD stage ===
def build(config):
    info("=== Starting BUILD stage ===")
    image = config["stages"]["build"]["image_name"]
    tag = config["stages"]["build"]["tag"]
    cmd = ["docker", "build", "-t", f"{image}:{tag}", "."]

    try:
        subprocess.run(cmd, check=True)
        success(f"✅ Build successful: {image}:{tag}")
        logger.info(f"Build successful: {image}:{tag}")
    except subprocess.CalledProcessError:
        error("❌ Build failed!")
        logger.error("Build failed")
        sys.exit(1)
# === TEST stage ===
def test(config):
    info("=== Starting TEST stage ===")

    test_cmd = config["stages"]["test"]["command"]
    logger.info(f"Running tests with: {test_cmd}")

    try:
        # Run tests inside the Docker container
        cmd = ["docker", "run", "--rm", "pydeployer:latest", "bash", "-c", test_cmd]
        subprocess.run(cmd, check=True)
        success("✅ Tests passed successfully!")
        logger.info("Tests passed successfully.")
    except subprocess.CalledProcessError:
        error("❌ Tests failed!")
        logger.error("Tests failed.")
        sys.exit(1)


# === Entry point for IPython ===
def run_stage(stage_name: str):
    config = load_config()

    if stage_name == "build":
        build(config)
    elif stage_name == "test":
        test(config)
    else:
        warn(f"⚠️ Stage '{stage_name}' not implemented yet.")
# === CLI entry (still works in normal terminal) ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PyDeployer CLI")
    parser.add_argument("stage", choices=["build", "test", "deploy", "rollback"])
    args = parser.parse_args()
    run_stage(args.stage)
