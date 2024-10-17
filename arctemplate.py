"""
Title: arctemplate.py
Authour: Patrick Harrison (000733057)
Date: Latest commit date

Purpose:
    The purpose of this script is to provide a 'ready-to-go' template for small
    arcpy scripts. CHANGE THIS PURPOSE STATEMENT to the actual purpose of the
    script.

    Due to a single file constraint put onto me, this file gets a bit crazy and
    really should be split into multiple modules.

Requirements:
    List or describe requirements for a successful running of the script.
    - arcpy

Use:
    `python <ScriptName>.py

    This script uses the walk method and dynamically sets the arcpy workspace
    based of the scripts location in the file directory. Due to this, unless
    changed, script must be at the root level of the project.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import arcpy


# --------------------
# Global Variables
# --------------------
# TODO: Set up argparse for these
ARCPY_LOG_LEVEL: int = logging.DEBUG # int enum
PYTHON_LOG_LEVEL: int = logging.DEBUG # int enum

WORKSPACE: Path = Path(os.getcwd()) # Stores location of the script as a Path object as default
COORDINATE_SYSTEM: arcpy.SpatialReference = arcpy.SpatialReference(4326)
OVERWRITE: bool = True


# --------------------
# Logging Setup
# --------------------
pylog_formatter = logging.Formatter("%(asctime)s [%(name)-16.16s] [%(levelname)-11.11s]  %(message)s")
file_handler = logging.FileHandler(f"{Path(__file__).name}.log")
file_handler.setFormatter(pylog_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(pylog_formatter)

logger = logging.getLogger(Path(__file__).name) # Python logger takes the dunder name of the file
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# get logger to reconize custom logging levels for arcpy
ARCPY_LOG_LEVEL_MAP: dict[int, str] = {#https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/getallmessages.htm
                                        10: "INFO",
                                        11: "DEFINITION",
                                        12: "START",
                                        13: "STOP",
                                        50: "WARNING",
                                        100: "ERROR",
                                        101: "EMPTY",
                                        102: "GDB_ERROR",
                                        200: "ABORT"
                                       }
for level, name in ARCPY_LOG_LEVEL_MAP.items():
    logging.addLevelName(level, name)

# defining a child class of logger to utilize new logging levels
class ArcpyMsgLogger(logging.Logger):
    """Custom logger for arcpy message levels

    It is not possible to set log level 0 messages since
    logging uses this as a NOTSET value and the logic behind
    this level won't filter any messages. To get around this,
    the info, definition, start and stop levels were all raised
    by 10 from the arcpy documentation. This will however overwrite
    the default DEBUG to be INFO

    the old info level (20) is not overwritten and can (but should not)
    be used. 
    """
    def info(self, message, *args, **kwargs):
        if self.isEnabledFor(10):
            self._log(10, message, args, **kwargs)
    def definition(self, message, *args, **kwargs):
        if self.isEnabledFor(11):
            self._log(11, message, args, **kwargs)
    def start(self, message, *args, **kwargs):
        if self.isEnabledFor(12):
            self._log(12, message, args, **kwargs)
    def stop(self, message, *args, **kwargs):
        if self.isEnabledFor(13):
            self._log(13, message, args, **kwargs)
    def warning(self, message, *args, **kwargs):
        if self.isEnabledFor(50):
            self._log(50, message, args, **kwargs)
    def error(self, message, *args, **kwargs):
        if self.isEnabledFor(100):
            self._log(100, message, args, **kwargs)
    def empty(self, message, *args, **kwargs):
        if self.isEnabledFor(101):
            self._log(101, message, args, **kwargs)
    def gdb_error(self, message, *args, **kwargs):
        if self.isEnabledFor(102):
            self._log(102, message, args, **kwargs)
    def abort(self, message, *args, **kwargs):
        if self.isEnabledFor(200):
            self._log(200, message, args, **kwargs)

logging.setLoggerClass(ArcpyMsgLogger) # use class with arcpy logging levels

arcpy_msg = logging.getLogger("ArcpyMessages")
arcpy_msg.addHandler(file_handler)
arcpy_msg.addHandler(console_handler)

# logger.setLevel(PYTHON_LOG_LEVEL)
logger.setLevel(logging.DEBUG)
arcpy_msg.setLevel(-1) # Always log all arcpy messages

def arcpy_log_messages(result: arcpy.Result|None=None) -> list:
    """Logger utility to log arcpy messages nicely.
    This utility will log arcpy messages using the custom logger.
    Unfortunate level conflicts with logging. See ArcPyMsgLogger
    docstring for more info
    """
    messages = arcpy.GetAllMessages()
    if result is not None:
        messages = result.GetAllMessages()

    for message in messages:
        msg_type = ARCPY_LOG_LEVEL_MAP[message[0]]
        if msg_type < 50:
            msg_type += 10
        msg_content = message[-1]
        arcpy_msg.log(msg_type, msg_content)

    return messages

def main() -> int:
    """Main program flow and entry point.

    returns:
        (int): Return code. 0 is successful, 1 is failure
    """
    logger.info("Logger info")
    arcpy_msg.log(20, "old info message")
    arcpy_msg.log(10, "new info message")
    arcpy_msg.info("method INFO MESSAGE")
    arcpy_msg.log(100, "method errorMESSAGE")
    print(arcpy_msg.getEffectiveLevel())
    return 0


if __name__ == "__main__":
    main()
