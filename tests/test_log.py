from loguru import logger

from pypaladin import conf, context
from concurrent import futures

CONF = conf.BaseAppConfig()


def main():
    CONF.setup()

    def do_something(x):
        context.set_trace(f"trace-{x}")
        for i in range(5):
            logger.info(f"foo {i}")

    context.set_vars(name="main_task")
    logger.debug("test log ...")
    logger.info("starting")
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for _ in executor.map(do_something, ["task1", "task2"]):
            pass
    logger.info("done")


if __name__ == "__main__":
    main()
