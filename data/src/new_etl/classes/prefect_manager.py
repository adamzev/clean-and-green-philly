from prefect import flow as prefect_flow
from prefect import task as prefect_task

from config.config import USE_PREFECT


def no_op_decorator(*args, **kwargs):
    _ = kwargs
    if args and callable(args[0]):
        return args[0]

    def wrapper(func):
        return func

    return wrapper


if USE_PREFECT:
    flow = prefect_flow
    task = prefect_task
else:
    # No-op fallback
    task = no_op_decorator
    flow = no_op_decorator
