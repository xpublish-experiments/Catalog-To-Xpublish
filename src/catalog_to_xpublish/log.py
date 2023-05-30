import logging
from pathlib import Path
from typing import (
    List,
    TypedDict,
    Optional,
)


class LoggingConfigDict(TypedDict):
    """A dictionary to hold the optional logging configuration args.

    NOTE: All arguments are optional.
    Attributes:
        level: The logging level.
        log_format: The formatting string of the log.
        date_format: The format of the date.
        log_file: The path to the log file.
        stream_handler: The stream handler or list of stream handlers.
    """
    level: Optional[str | int]
    log_format: Optional[str]
    date_format: Optional[str]
    log_file: Optional[str | Path]
    stream_handler: Optional[logging.Handler | List[logging.Handler]]


class APILogging:
    """A class to hold the logging configuration."""

    LOGGER: logging.Logger | None = None
    LOG_NAME: str = 'catalog_to_xpublish'
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '[%(asctime)s] %(levelname)s - %(message)s'
    DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%S'

    @staticmethod
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
            level = logging.getLevelNamesMapping()[level]
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

    @staticmethod
    def __validate_log_file(
        log_file: str | Path,
    ) -> Path:
        """Validate the logging log_file."""
        if isinstance(log_file, str):
            log_file = Path(log_file)
        if not isinstance(log_file, Path):
            raise TypeError(
                f'log_file must be a str or Path, not {type(log_file)}',
            )
        if not log_file.parent.exists():
            raise ValueError(
                f'directory={log_file.parent} does not exist.',
            )
        if not log_file.suffix == '.log':
            raise ValueError(
                f'log_file={log_file} must have a .log extension.',
            )
        return log_file

    @staticmethod
    def __validate_handlers(
        stream_handlers: logging.Handler | List[logging.Handler],
        log_file: Path | None,
    ) -> List[logging.Handler]:
        """Validate the logging handlers."""

        # parse any provided stream handlers
        if isinstance(stream_handlers, logging.Handler):
            handlers = [stream_handlers]
        elif isinstance(stream_handlers, list):
            handlers = stream_handlers
        else:
            raise TypeError(
                f'stream_handler must be a logging.Handler or List[logging.Handler], '
                f'not {type(stream_handlers)}',
            )

        # add a file handler if a log_file was provided
        if log_file:
            handlers.append(logging.FileHandler(log_file))

        return handlers

    @classmethod
    def config_logger(
        cls,
        config_dict: Optional[LoggingConfigDict] = None,
    ) -> None:
        """Configure the logger.

        Arguments:
            config_dict: A dictionary of optional logging configuration args.

        Returns:
            None. Sets a global LOGGER variable.
        """
        if not config_dict:
            config_dict = {}

        # parse the config_dict
        level: str | int = config_dict.get('level', cls.LOG_LEVEL)
        log_format: str = config_dict.get('log_format', cls.LOG_FORMAT)
        date_format: str = config_dict.get('date_format', cls.DATE_FORMAT)
        log_file: str = config_dict.get('log_file', None)
        stream_handlers: logging.Handler | List[logging.Handler] = config_dict.get(
            'stream_handler',
            logging.StreamHandler(),
        )

        # validate the level and log_file
        level: int = cls.__validate_level(level)
        if log_file:
            log_file: Path = cls.__validate_log_file(log_file)

        # get the handlers
        handlers: List[logging.Handler] = cls.__validate_handlers(
            stream_handlers=stream_handlers,
            log_file=log_file,
        )

        # config the logger
        logging.basicConfig(
            level=level,
            format=log_format,
            datefmt=date_format,
            handlers=handlers,
            force=True,
        )

        # set the logger as a class attribute
        cls.LOGGER = logging.getLogger()
        cls.LOGGER.name = cls.LOG_NAME
