from __future__ import annotations

import asyncio
import datetime as dt
from typing import Callable, Iterable

import pytz
import schedule


def _now(tz: str):
    if tz == "local":
        return dt.datetime.now()
    return dt.datetime.now(pytz.timezone(tz))


def schedule_daily(times: Iterable[str], timezone: str, job: Callable[[], None]) -> None:
    for t in times:
        schedule.every().day.at(t).do(job)

    # Informative no-op: the job will run when the time hits in local clock; if timezone != local,
    # we still rely on the system clock to be in that timezone or use container TZ.


def run_loop(block: bool = True):
    async def _tick():
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    if block:
        asyncio.run(_tick())
    else:
        asyncio.create_task(_tick())


