import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s', level = logging.DEBUG)

logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')