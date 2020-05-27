"""Standard logging for TANGO devices."""
import enum
import inspect
import logging
import pathlib
import sys
import threading
import typing

# Be able to cope if tango is not installed.
try:
    import tango.server
    _device_class = tango.server.Device
except ImportError:
    class _NoDev:
        pass
    _device_class = _NoDev
    tango = sys.modules[__name__]

from . import core_logging


class LogLevel(enum.Enum):
    """
    Fallback enum for the case where tango is not installed.
    """
    LOG_FATAL = logging.CRITICAL
    LOG_ERROR = logging.ERROR
    LOG_WARN = logging.WARNING
    LOG_INFO = logging.INFO
    LOG_DEBUG = logging.DEBUG
    LOG_OFF = logging.NOTSET


_TANGO_TO_PYTHON = {
    tango.LogLevel.LOG_FATAL: logging.CRITICAL,
    tango.LogLevel.LOG_ERROR: logging.ERROR,
    tango.LogLevel.LOG_WARN: logging.WARNING,
    tango.LogLevel.LOG_INFO: logging.INFO,
    tango.LogLevel.LOG_DEBUG: logging.DEBUG,
    tango.LogLevel.LOG_OFF: logging.NOTSET
}


def to_python_level(tango_level: tango.LogLevel) -> int:
    """Convert a TANGO log level to a Python one.

    :param tango_level: TANGO log level
    :returns: Python log level
    """
    return _TANGO_TO_PYTHON[tango_level]


class LogManager:
    """Redirect log messages.

    This is redundant from Python 3.8 as the logging module then supports
    a "stacklevel" keyword.
    """

    def __init__(self):
        """Initialise the constructor."""
        self.frames = {}

    def make_fn(self, level: int) -> typing.Callable:
        """Create a redirection function.

        :param level: to log. default: INFO
        :returns: logging function to call
        """
        return lambda _, msg, *args: self._log_it(level, msg, *args)

    def _log_it(self, level: int, msg: str, *args) -> None:
        # There are two levels of indirection.
        # Remember the right frame in a thread-safe way.
        self.frames[threading.current_thread()] = inspect.stack()[2]
        logging.log(level, msg, *args)


class TangoFormatter(core_logging.SkaFormatter):
    """Replace the stack frame with the right one.

    This is redundant from Python 3.8 as the logging module then supports
    a "stacklevel" keyword.
    """

    def __init__(self, *tags):
        """Initialise the constructor."""
        super().__init__(*tags)
        self.log_man = LogManager()

    def format(self, record: logging.LogRecord) -> str:
        # If the record originates from this module, insert the right frame info.
        if record.pathname == __file__:
            thread = threading.current_thread()
            # The thread should be in the dictionary, but may not be if the
            # module has been reloaded e.g. by unit test.
            if thread in self.log_man.frames:
                frame = self.log_man.frames[thread]
                record.funcName = frame.function
                record.filename = pathlib.Path(frame.filename).name
                record.lineno = frame.lineno
        return super().format(record)


def init(level=tango.LogLevel.LOG_INFO, name=None, device_name='',
         device_class=_device_class) -> logging.Logger:
    """Initialise logging for a TANGO device.

    This modifies the logging behaviour of the device class.

    :param name: of logger, top-level if None. default: None
    :param level: to log. default: INFO
    :param device_name: name of TANGO device. default: ''
    :param device_class: class object. default: tango.server.Device
    :returns: logger object
    """
    # Monkey patch the tango device logging to redirect to python.
    fmt = TangoFormatter(device_name)
    device_class.debug_stream = fmt.log_man.make_fn(logging.DEBUG)
    device_class.info_stream = fmt.log_man.make_fn(logging.INFO)
    device_class.warn_stream = fmt.log_man.make_fn(logging.WARNING)
    device_class.error_stream = fmt.log_man.make_fn(logging.ERROR)
    device_class.fatal_stream = fmt.log_man.make_fn(logging.CRITICAL)

    # Now initialise the logging.
    log = core_logging.init(name=name, level=to_python_level(level),
                            formatter=fmt)
    device_class.get_logger = lambda self: log
    return log
