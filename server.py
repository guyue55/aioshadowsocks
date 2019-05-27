import asyncio
import logging
import os
import signal

from shadowsocks.mdb.models import User
from shadowsocks.utils import init_logger_config, init_memory_db


def cron_task(sync_time, use_json=False):

    loop = asyncio.get_event_loop()
    try:
        if use_json:
            User.create_or_update_from_json("userconfigs.json")
        else:
            User.create_or_update_from_remote()
        User.flush_data_to_remote()
        User.init_user_servers()
    except Exception as e:
        logging.warning(f"sync user error {e}")
    loop.call_later(sync_time, cron_task, sync_time, use_json)


def run_servers():
    def shutdown():
        User.shutdown_user_servers()
        loop.stop()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    use_json = False if os.getenv("SS_API_ENDPOINT") else True
    sync_time = int(os.getenv("SS_SYNC_TIME", 60))
    try:
        cron_task(sync_time, use_json)
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("正在关闭所有ss server")
        shutdown()


if __name__ == "__main__":
    init_logger_config(log_level=os.getenv("SS_LOG_LEVEL", "info"))
    init_memory_db()
    run_servers()
