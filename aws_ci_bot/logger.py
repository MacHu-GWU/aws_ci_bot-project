# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger("ci_bot")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s; %(levelname)-8s; %(message)s")
)
logger.addHandler(stream_handler)


def header(msg: str, char: str, length: int, corner_char=""):
    msg = f" {msg} "
    template = "{corner_char}{{msg:{char}^{length}}}".format(
        char=char,
        length=length,
        corner_char=corner_char,
    )
    logger.info(template.format(msg=msg))


tab = "  "


def info(msg: str, indent=0):
    return logger.info(f"{tab * indent}{msg}")
