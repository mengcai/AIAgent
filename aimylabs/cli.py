from __future__ import annotations

import argparse
import asyncio
import os
from typing import Optional

from dotenv import load_dotenv

from .agent import AimylabsAgent
from .config import load_config
from .scheduler import run_loop, schedule_daily


def _load_env():
    # Load .env if present
    env_candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "env"),
        os.path.join(os.getcwd(), "env.sample"),
    ]
    for path in env_candidates:
        if os.path.exists(path):
            load_dotenv(path)


def cmd_run(dry_run: Optional[bool] = None):
    _load_env()
    cfg = load_config()
    if dry_run is not None:
        cfg.app.dry_run = dry_run
    agent = AimylabsAgent(cfg)
    urls = asyncio.run(agent.run_once())
    print(f"Posted {len(urls)} items" + (" (dry-run)" if cfg.app.dry_run else ""))


def cmd_schedule():
    _load_env()
    cfg = load_config()
    agent = AimylabsAgent(cfg)

    def _job():
        print("Running scheduled cycle...")
        asyncio.run(agent.run_once())

    schedule_daily(cfg.app.post_times, cfg.app.timezone, _job)
    print(f"Scheduler started for times: {cfg.app.post_times} (TZ: {cfg.app.timezone})")
    run_loop(block=True)


def main():
    parser = argparse.ArgumentParser(prog="aimylabs", description="Aimylabs — AI/Web3 News-to-X agent")
    sub = parser.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Run one collection/summarization/posting cycle")
    run_p.add_argument("--dry-run", action="store_true", help="Don't post, just print")

    sub.add_parser("schedule", help="Run the scheduler forever")

    args = parser.parse_args()
    if args.cmd == "run":
        cmd_run(dry_run=True if args.dry_run else None)
    elif args.cmd == "schedule":
        cmd_schedule()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


