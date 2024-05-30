import logging
import logging.config


def setup_logger():
    # Определите конфигурацию логгера
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            # 'file': {
                # 'level': 'DEBUG',
                # 'class': 'logging.FileHandler',
                # 'formatter': 'standard',
                # 'filename': os.path.join(os.path.dirname(__file__), 'app.log')
            # },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True
            },
        }
    }

    # Настройка логгера с использованием конфигурации
    logging.config.dictConfig(logging_config)


# Функция для получения логгера в других модулях
def get_logger(name):
    return logging.getLogger(name)
