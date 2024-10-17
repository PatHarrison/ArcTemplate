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
    - arcpy / ESRI arc environment and licensing

Use:
    `python <ScriptName>.py

    This script uses the walk method and dynamically sets the arcpy workspace
    based of the scripts location in the file directory. Due to this, unless
    changed, script must be at the root level of the project.
"""

import os
import argparse
import logging
from pathlib import Path

import arcpy


# --------------------
# Logging Setup
# --------------------
def setup_logging(logger_level: int|None=None,
                  arcpy_msgs_level: int=-1
                  ) -> list[logging.Logger]:
    """Wraper for logging set.
    Sets up a python logger and a logger object to handle arcpy
    messages.

    parameters:
        logger-level (int|None): caputre log level for python script
        arcpy_msgs (int): capture log level for arcpy messages. defaults to logging all messages.

    returns:
        python logger (logging.Logger), arcpy message logger (logging.Logger)
    """
    # General Logging setup
    pylog_formatter = logging.Formatter("%(asctime)s [%(name)-16.16s] [%(levelname)-11.11s]  %(message)s")
    file_handler = logging.FileHandler(f"{Path(__file__).name}.log")
    file_handler.setFormatter(pylog_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(pylog_formatter)

    # Create python logger
    logger = logging.getLogger(Path(__file__).name) # Python logger takes the dunder name of the file
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


    # get logger to reconize custom logging levels for arcpy
    #https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/getallmessages.htm
    arcpy_log_level_map: dict[int, str] = {
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
    for level, name in arcpy_log_level_map.items():
        logging.addLevelName(level, name)

    # defining a child class of logger to utilize new logging levels
    class ArcpyMsgLogger(logging.Logger):
        """Custom logger for arcpy message levels

        It is not possible to set log level 0 messages since
        logging uses this as a NOTSET value and the logic behind
        this level won't filter any messages. To get around this,
        the info, definition, start and stop levels were all raised
        by 10 from the arcpy documentation. This will however overwrite
        the default DEBUG to be INFO. The default critical level is
        also overwritten by the arpy warning level.

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

    # Create arcpy message logger
    arcpy_msgs = logging.getLogger("ArcpyMessages")
    arcpy_msgs.addHandler(file_handler)
    arcpy_msgs.addHandler(console_handler)

    # Set logger levels
    logger.setLevel(logger_level)
    arcpy_msgs.setLevel(arcpy_msgs_level)

    return logger, arcpy_msgs


def arcpy_log_messages(result: arcpy.Result|None=None) -> list:
    """Logger utility to log arcpy messages nicely.
    This utility will log arcpy messages using the custom logger.
    Unfortunate level conflicts with logging. See ArcPyMsgLogger
    docstring for more info
    """
    if result is not None:
        messages = result.GetAllMessages()
    else:
        message = arcpy.GetAllMessages()

    for message in messages:
        msg_type = arcpy_log_level_map[message[0]]
        if msg_type < 50:
            msg_type += 10
        msg_content = message[-1]
        arcpy_msg.log(msg_type, msg_content)

    return messages


# --------------------
# General Setup
# --------------------
def print_header(msg: str) -> int:
    """Printing Utility for nice boxes.
    Adapted from:
        https://stackoverflow.com/questions/39969064/how-to-print-a-message-box-in-python 
    parameters:
        msg (str): Message to be printed
        indent (int): number of spaces for the message to be away from the edge of the box
        width (int|None): defaults to the max line length. Can be set larger.
    Returns:
        (int): 0 for success, else failure.
    Output:
        stdout: nicely formatted messages in boxes
    """
    lines = msg.split("\n")
    width = int(0.33 * os.get_terminal_size()[0])
    box = f"╔{'═' * width}╗\n"  # upper_border
    box += "".join([f"║{line:^{width}}║\n" for line in lines])
    box += f"╚{'═' * width}╝"  # lower_border
    print(box)


# --------------------
# Program Workflow
# --------------------
def main(workspace: Path,
         log_level: int,
         arcpy_msgs_level: int|None=None
         ) -> int:
    """Main program flow and entry point.

    parameters:
        log_level (int): Workflow logger level
        arcpy_msgs_level (int): arcpy messages level to be captured

    returns:
        (int): Return code. 0 is successful, 1 is failure
    """
    logger, arcpy_msgs = setup_logging(log_level, arcpy_msgs_level)
    print_header("Program Started")
    logger.info("Starting workflow")

    logger.info("Success. Exiting...")
    return 0


if __name__ == "__main__":

    # --------------------
    # CLI arguments setup
    # --------------------
    parser = argparse.ArgumentParser(
            description="A template script for arcpy workflows"
            )
    parser.add_argument("-v", "--verbose", help="Set logger level to info",
                        action="store_true")
    parser.add_argument("-vv", "--very-verbose", help="Set logger level to debug",
                        action="store_true")
    parser.add_argument("--workspace", type=str, required=False,
                        help="set the workspace path of the project. the default workspace is set to the scripts path.",
                        default=str(os.getcwd())
                        )
    args = parser.parse_args()

    # Decode logging levels
    if args.very_verbose:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    
    # --------------------
    # Call Workflow
    # --------------------
    main(workspace=Path(args.workspace), log_level=log_level, arcpy_msgs_level=0)
