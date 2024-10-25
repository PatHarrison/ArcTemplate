"""
Title: arctemplate.py
Authour: Patrick Harrison (000733057)
Date: Latest commit date

Purpose:
    The purpose of this script is to provide a 'ready-to-go' template 
    for small arcpy scripts. CHANGE THIS PURPOSE STATEMENT to the actual
    purpose of the script.

    Due to a single file constraint put onto me, this file gets a bit 
    crazy and really should be split into multiple modules.

Requirements:
    List or describe requirements for a successful running of the 
    script.
    - arcpy / ESRI arc environment and licensing

Use:
    `python <ScriptName>.py

    This script uses the walk method and dynamically sets the arcpy 
    workspace based of the scripts location in the file directory. Due
    to this, unless changed, script must be at the root level of the 
    project.
"""

import os
import argparse
import logging
from logging import Logger
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any, Iterable, Iterator, List, Tuple, Unknown
from tqdm import tqdm

import arcpy
from arcpy import Result


# --------------------
# Types
# --------------------
ArcpyMessages = List[List[Unknown]]


# --------------------
# Logging Setup
# --------------------
def setup_logging(
    logger_level: int, arcpy_msgs_level: int = -1,
    console_logging: bool = False
) -> Tuple[Logger, Logger]:
    """Wraper for logging set.
    Sets up a python logger and a logger object to handle arcpy
    messages.

    parameters:
        logger_level (int|None): caputre log level for python script
        arcpy_msgs (int): capture log level for arcpy messages. defaults
            to logging all messages.
        console_logging (bool): Flag to add logging to stdout.
    returns:
        (Tuple[Logger, Logger]): Tuple of python and arcpy message loggers
    """
    format_str: logging.Formatter = logging.Formatter(
        "%(asctime)s [%(name)-16.16s] [%(levelname)-11.11s]  %(message)s"
    )
    file_handler: logging.FileHandler = logging.FileHandler(
        f"{Path(__file__).stem}.log", mode="w"
    )
    file_handler.setFormatter(format_str)
    console_handler: logging.StreamHandler = logging.StreamHandler()
    console_handler.setFormatter(format_str)

    # Python logger takes the dunder name of the file
    logger: Logger = logging.getLogger(Path(__file__).name)
    logger.addHandler(file_handler)

    # get logger to reconize custom logging levels for arcpy
    # Levels below 50 are increased by 20 to deal with the 
    # Clash with level 0
    # https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/getallmessages.htm
    arcpy_log_level_map: dict[int, str] = {
        20: "INFO",
        21: "DEFINITION",
        22: "START",
        23: "STOP",
        50: "WARNING",
        100: "ERROR",
        101: "EMPTY",
        102: "GDB_ERROR",
        200: "ABORT",
    }
    for level, name in arcpy_log_level_map.items():
        logging.addLevelName(level, name)

    # Create arcpy message logger
    arcpy_msgs: logging.Logger = logging.getLogger("ArcpyMessages")
    arcpy_msgs.addHandler(file_handler)

    if console_logging: # If user wants logging to stdout
        arcpy_msgs.addHandler(console_handler)
        logger.addHandler(console_handler)

    # Set logger levels
    logger.setLevel(logger_level)
    arcpy_msgs.setLevel(arcpy_msgs_level)

    return logger, arcpy_msgs


def get_script_logger() -> Logger:
    """Utility for getting the script logger."""
    return logging.getLogger(Path(__file__).name)


def get_msg_logger() -> Logger:
    """Utility to get the arcpy message logger."""
    return logging.getLogger("ArcpyMessages")


def arcpy_log_messages(
    result: arcpy.Result, msg_logger: Logger = get_msg_logger()
) -> ArcpyMessages:
    """Logger utility to log arcpy messages nicely.
    This utility will log arcpy messages using the custom logger.
    Unfortunate level conflicts with logging. See ArcPyMsgLogger
    docstring for more info

    parameters:
        result (Result): result object to get the messages from.
        msg_logger (Logger): logger for handling arcpy messages.
    returns:
        (list[str]): list of arcpy messages
    """
    messages: Unknown = result.getAllMessages()
    result_id = result.resultID
    for message in messages:
        msg_type = message[0]
        if msg_type < 50:  # worksaround for log level 0 from arcpy
            msg_type += 20
        msg_content = message[-1]
        msg_logger.log(msg_type, result_id + msg_content)

    return messages


@contextmanager
def arcpy_severity_context(level: int, logger: Logger = get_script_logger()):
    """Context manager to temporarily set ArcPy severity level.
    This will raise and exception for warnings when severity is
    set to 1, and only raise and exception for errors when severity
    is set to 2.

    parameters:
        level (int): level to set severity to in context block.
        logger (Logger): logger object to use.
    yields:
        None
    """
    original_level: int = arcpy.GetSeverityLevel()

    arcpy.SetSeverityLevel(level)
    logger.debug(f"arcpy severity set to level {level}")

    try:
        yield
    finally:  # reset severity level
        arcpy.SetSeverityLevel(original_level)
        logger.debug(f"arcpy severity level set to {original_level}")


def log_messages(severity=2, logger: Logger = get_script_logger()) -> object:
    """Warpper function for arcpy logging and error handling.
    This can be used to warp a function definition like a decorator,
    or when calling an arcpy function as follows:
        `log_messages(severity=1)(arcpy.some.toolfunc)(*args_for_tool)`
    severity level is set to 2 by default and only errors will cause a tool
    failure.

    parameters:
        severity (int): what to set the severity level to.
        logger (Logger): script logger to log function calls.
    returns:
        decorator (object)
    """
    def decorator(func):
        def wrapped_func(*args, **kwargs):
            """Warps an arcpy function and handles messages
            arcpy.GetAllMessages will be used if tool fails, otherwise
            results are logged with the result id.
            """
            with arcpy_severity_context(severity):
                logger.info(f"{func.__name__} called with {args}")
                try:
                    result = func(*args, **kwargs) # Run tool
                except arcpy.ExecuteError:
                    logger.error(f"ArcPy encounted an error")
                    arcpy.GetAllMessages()
                    raise
                except arcpy.ExecuteWarning:
                    # Arcpy will only throw this if severity level is 1
                    logger.error(f"ArcPy encounted an warning and will stop")
                    arcpy.GetAllMessages()
                    raise
                except Exception as e:
                    logger.error(f"Unexpected Error in {func.__name__}: {e}")
                    arcpy.GetAllMessages()
                    raise
                else:
                    logger.info(f"{func.__name__} exectued successfully")
                    arcpy_log_messages(result) # log results with result id
                    return result

        return wrapped_func

    return decorator


# --------------------
# General Utilities
# --------------------
def print_header(msg: str, width_factor=0.33) -> int:
    """Printing Utility for nice boxes.
    Adapted from:
    https://stackoverflow.com/questions/39969064/how-to-print-a-message-box-in-python
    if printing the box fails, it will just print the msg handed to it.

    parameters:
        indent (int): number of spaces for the message to be away from the edge
            of the box
        width_factor (int): defaults to 0.33. Sets the percentage width of the
            box for the width of the console output environment.
    Returns:
        (int): 0 for success, else failure.
    Output:
        stdout: nicely formatted messages in boxes
    """
    try:
        lines: List[str] = msg.split("\n")
        width: int = int(width_factor * os.get_terminal_size()[0])
        box: str = f"╔{'═' * width}╗\n"  # upper_border
        box += "".join([f"║{line:^{width}}║\n" for line in lines])
        box += f"╚{'═' * width}╝"  # lower_border
        print("\n\n")
        print(box)
    except:
        print(msg)
        return 1

    return 0


# --------------------
# Program Workflow
# --------------------
def main(
        workspace: Path, log_level: int,
        arcpy_msgs_level: int|None = None
) -> int:
    """Main program flow and entry point.

    parameters:
        log_level (int): Workflow logger level
        arcpy_msgs_level (int): arcpy messages level to be captured
    returns:
        (int): Return code. 0 is successful, 1 is failure
    """
    with arcpy.EnvManager(workspace=workspace):
        pass
    logger, arcpy_msgs = setup_logging(log_level, arcpy_msgs_level)
    print_header("Program Started")
    logger.info("Starting workflow")

    logger.info("Success. Exiting...")
    return 0


if __name__ == "__main__":
    # --------------------
    # CLI arguments setup
    # --------------------
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="A template script for arcpy workflows"
    )
    parser.add_argument(
        "-v", "--verbose", help="Set logger level to info", action="store_true"
    )
    parser.add_argument(
        "-vv", "--very-verbose", help="Set logger level to debug", action="store_true"
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=str,
        required=False,
        help=(
            "set the workspace path of the project. the default "
            "workspace is set to the scripts path."
        ),
        default=str(os.getcwd()),
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Sets the arcpy.env.overwriteOutput to false.",
        action="store_false",
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
