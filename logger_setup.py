import logging
logger = logging.getLogger("dark-photon-event-gen")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter('(%(asctime)s) : %(filename)s - %(levelname)s : %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)