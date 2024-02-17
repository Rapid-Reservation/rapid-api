# Log information for logging, also might offload to blob storage or something?
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os


date = datetime.datetime.now().strftime("%Y-%m-%d")
log_filename = os.path.join (f"logs/{date}.log")

logger = logging.getLogger()
logFormatter = logging.Formatter("%(asctime)s-%(levelname)s-%(name)s-%(message)s", datefmt="%H:%M:%S")

# log to console
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

# log to log/file.log
fileHandler = RotatingFileHandler(log_filename)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


#logging.basicConfig(filename=log_filename, format="%(levelname)s:%(name)s:%(message)s")