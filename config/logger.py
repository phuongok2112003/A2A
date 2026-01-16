import logging
import sys
from .settings import settings

class Logger:
  def __init__(self):
    self.logger = logging.getLogger(settings.APP_NAME)
    
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s","%Y-%m-%d %H:%M:%S")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    self.logger.addHandler(console_handler)

  def debug(self, msg: str):
    self.logger.setLevel(logging.DEBUG)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "DEBUG"
      }
    }
    self.logger.debug(msg, extra=extra)

  def info(self, msg: str):
    self.logger.setLevel(logging.INFO)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "INFO"
      }
    }
    self.logger.info(msg, extra=extra)

  def warning(self, msg: str):
    self.logger.setLevel(logging.WARN)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "WARN"
      }
    }
    self.logger.warning(msg, extra=extra)
  
  def error(self, msg):
    self.logger.setLevel(logging.ERROR)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "ERROR"
      }
    }
    self.logger.error(msg, extra=extra)
  
  def exception(self, msg):
    self.logger.setLevel(logging.ERROR)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "EXCEPTION"
      }
    }
    self.logger.exception(msg, extra=extra)

  def fatal(self, msg):
    self.logger.setLevel(logging.ERROR)
    extra = {
      'elastic_fields': {
          'version': 'python version: ' + repr(sys.version_info),
          'level': "FATAL"
      }
    }
    self.logger.fatal(msg, extra=extra)

log = Logger()
