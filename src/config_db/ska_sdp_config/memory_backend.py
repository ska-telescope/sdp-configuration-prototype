"""
This module implements an in-memory database backend, principally for testing purposes. In
principle it should behave in the same way as the etcd backend.
No attempt has been made to make it thread-safe, so it probably isn't.
"""
from typing import List, Callable

from ska_sdp_config.backend import (
    _depth, _tag_depth, _untag_depth, _check_path, ConfigCollision, ConfigVanished)


def _op(path: str, value: str,
        to_check: Callable[[str], None], to_do: Callable[[str, str], None]):
    _check_path(path)
    tag = _tag_depth(path)
    to_check(tag)
    to_do(tag, value)


class MemoryBackend:
    """
    In-memory backend implementation, principally for testing.
    """
    def __init__(self):
        """
        Constructor.
        """
        self.dict = {}

    def lease(self, *args, **kwargs) -> 'Lease':
        """
        Generate a dummy lease object. This currently has no additional methods.
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: dummy lease object
        """
        class Lease:
            """ Dummy lease class. """
            pass
        return Lease()

    def txn(self, *args, **kwargs) -> 'MemoryTransaction':
        """
        Create an in-memory "transaction".
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: transaction object
        """
        return MemoryTransaction(self)

    def get(self, path: str) -> str:
        """
        Get the value at the given path
        :param path: to lookup
        :return: the value
        """
        return self.dict.get(_tag_depth(path), None)

    def _put(self, path: str, value: str) -> None:
        self.dict[path] = value

    def _check_exists(self, path: str) -> None:
        if path not in self.dict.keys():
            raise ConfigVanished(path, "{} not in dictionary".format(path))

    def _check_not_exists(self, path: str) -> None:
        if path in self.dict.keys():
            raise ConfigCollision(path, "path {} already in dictionary".format(path))

    def create(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Create an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, value, self._check_not_exists, self._put)

    def update(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Update an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, value, self._check_exists, self._put)

    def delete(self, path, *args, **kwargs) -> None:
        """
        Delete an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, None, self._check_exists, lambda t, _: self.dict.pop(t))

    def list_keys(self, path: str) -> List[str]:
        """
        Get a list of the keys at the given path. In common with the etcd backend, the structure is
        "flat" rather than a real hierarchy, even though it looks like one.
        :param path:
        :return: list of keys
        """
        # Match only at this depth level. Special case for top level.
        if path == '/':
            p = path
            depth = 1
        else:
            p = path.rstrip('/')
            depth = _depth(p) + 1
        tag = _tag_depth(p, depth=depth)
        return sorted([_untag_depth(k) for k in self.dict.keys() if k.startswith(tag)])

    def close(self) -> None:
        """
        This does nothing.
        :return: nothing
        """
        pass


class MemoryTransaction:
    """
    Transaction wrapper around the backend implementation. Transactions always succeed if they
    are valid, so there is no need to loop; however the iterator is supported for compatibility
    with the etcd backend.
    """
    def __init__(self, backend: MemoryBackend):
        """
        Constructor.
        :param backend: to wrap
        """
        self.backend = backend

    def __iter__(self):
        """
        Iterator that just returns this object.
        :return: this object
        """
        yield self

    def commit(self) -> None:
        """
        This does nothing.
        :return: nothing
        """
        pass

    def get(self, path: str) -> str:
        """
        Get the value at the given path
        :param path: to lookup
        :return: the value
        """
        return self.backend.get(path)

    def create(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Create an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.create(path, value)

    def update(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Update an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.update(path, value)

    def delete(self, path, *args, **kwargs):
        """
        Delete an entry at the given path.
        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.delete(path)

    def list_keys(self, path: str) -> List[str]:
        """
        Get a list of the keys at the given path. In common with the etcd backend, the structure is
        "flat" rather than a real hierarchy, even though it looks like one.
        :param path:
        :return: list of keys
        """
        return self.backend.list_keys(path)

    def loop(self, *args, **kwargs) -> None:
        """
        This does nothing.
        :return: nothing
        """
        pass

