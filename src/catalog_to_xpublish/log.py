import logging
from pathlib import Path
import enum
from typing import (
    TypedDict,
    Optional,
)

LOGGER = logging.getLogger(__name__)


class LoggingConfigDict(TypedDict):
    """A dictionary to hold the logging configuration."""
    level: Optional[str | int]
    log_name: Optional[str]
    log_format: Optional[str]
    date_format: Optional[str]
    filename: Optional[str | Path]

# get rid of this


class LoggingLevel(enum.Enum):
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


DEFAULT_LOGGER_NAME: str = 'catalog_to_xpublish'
LOG_NAME: str = DEFAULT_LOGGER_NAME
LOG_LEVEL: str = 'DEBUG'
LOG_FORMAT: str = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%S'


def __validate_level(
    level: str | int,
) -> int:
    """Validate the logging level."""
    if isinstance(level, str):
        level = level.upper()
        if level not in logging.getLevelNamesMapping().keys():
            raise ValueError(
                f'level={level} is not a valid string logging level. '
                f'Choose from {logging.getLevelNamesMapping().keys()}',
            )
        level = LoggingLevel[level].value
    elif isinstance(level, int):
        if level not in logging.getLevelNamesMapping().values():
            raise ValueError(
                f'level={level} is not a valid int logging level. '
                f'Choose from {logging.getLevelNamesMapping().values()}',
            )
    else:
        raise TypeError(
            f'level must be a str or int, not {type(level)}',
        )
    return level


def __validate_filename(
    filename: str | Path,
) -> Path:
    """Validate the logging filename."""
    if isinstance(filename, str):
        filename = Path(filename)
    if not isinstance(filename, Path):
        raise TypeError(
            f'filename must be a str or Path, not {type(filename)}',
        )
    if not filename.parent.exists():
        raise ValueError(
            f'directory={filename.parent} does not exist.',
        )
    if not filename.suffix == '.log':
        raise ValueError(
            f'filename={filename} must have a .log extension.',
        )
    return filename


def config_logger(
    config_dict: Optional[LoggingConfigDict] = None,
) -> None:
    """Configure the logger."""
    if not config_dict:
        config_dict = {}

    # parse the config_dict
    level: str | int = config_dict.get('level', LOG_LEVEL)
    log_format: str = config_dict.get('log_format', LOG_FORMAT)
    date_format: str = config_dict.get('date_format', DATE_FORMAT)
    filename: str = config_dict.get('filename', None)
    stream_handler: logging.Handler = config_dict.get(
        'stream_handler',
        logging.StreamHandler(),
    )

    # validate the config_dict
    level = __validate_level(level)

    if filename:
        filename = __validate_filename(filename)

    # TODO: figure out why logging is being annoying
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        # filename=filename,
        handlers=[stream_handler],
        force=True,
    )
    logging.getLogger(LOG_NAME)
    print()
