import logging
from .protocol import Protocol

from pickle import loads, dumps


class Client(object):
    """
    This is intended to be a client class which implement standard cache interface that common libs do.
    """
    def __init__(self, servers=['127.0.0.1:11211'], username=None,
                 password=None, compression=None):
        """
        :param servers: A list of servers with ip[:port] or unix socket.
        :type servers: list
        :param username: If your server have auth activated, provide it's username.
        :type username: basestring
        :param password: If your server have auth activated, provide it's password.
        :type password: basestring
        """
        self.username = username
        self.password = password
        self.compression = compression
        self.set_servers(servers)


    @property
    def servers(self):
        for server in self._servers:
            yield server

    def set_servers(self, servers):
        """
        Iter to a list of servers and instantiate Protocol class.

        :param servers: A list of servers
        :type servers: list
        :return: Returns nothing
        :rtype: None
        """
        if isinstance(servers, str):
            servers = [servers]

        assert servers, "No memcached servers supplied"
        self._servers = [Protocol(server, self.username, self.password,
                                  self.compression) for server in servers]

    def _set_retry_delay(self, value):
        for server in self._servers:
            server.set_retry_delay(value)

    def enable_retry_delay(self, enable):
        """
        Enable or disable delaying between reconnection attempts.

        The first reconnection attempt will always happen immediately, so intermittent network
        errors don't cause caching to turn off.  The retry delay takes effect after the first
        reconnection fails.

        The reconnection delay is enabled by default for TCP connections, and disabled by
        default for Unix socket connections.
        """
        # The public API only allows enabling or disabling the delay, so it'll be easier to
        # add exponential falloff in the future.  _set_retry_delay is exposed for tests.
        self._set_retry_delay(5 if enable else 0)

    def get(self, key, get_cas=False):
        """
        Get a key from server.

        :param key: Key's name
        :type key: basestring
        :param get_cas: If true, return (value, cas), where cas is the new CAS value.
        :type get_cas: boolean
        :return: Returns a key data from server.
        :rtype: object
        """
        for server in self.servers:
            value, cas = server.get(key)
            if value is not None:
                if get_cas:
                    return value, cas
                else:
                    return value

    def gets(self, key):
        """
        Get a key from server, returning the value and its CAS key.

        This method is for API compatibility with other implementations.

        :param key: Key's name
        :type key: basestring
        :return: Returns (key data, value), or (None, None) if the value is not in cache.
        :rtype: object
        """
        for server in self.servers:
            value, cas = server.get(key)
            if value is not None:
                return value, cas
        return None, None

    def get_multi(self, keys, get_cas=False):
        """
        Get multiple keys from server.

        :param keys: A list of keys to from server.
        :type keys: list
        :param get_cas: If get_cas is true, each value is (data, cas), with each result's CAS value.
        :type get_cas: boolean
        :return: A dict with all requested keys.
        :rtype: dict
        """
        d = {}
        if keys:
            for server in self.servers:
                results = server.get_multi(keys)
                if not get_cas:
                    for key, (value, cas) in list(results.items()):
                        results[key] = value
                d.update(results)
                keys = [_ for _ in keys if not _ in d]
                if not keys:
                    break
        return d

    def set(self, key, value, time=0):
        """
        Set a value for a key on server.

        :param key: Key's name
        :type key: basestring
        :param value: A value to be stored on server.
        :type value: object
        :param time: Time in seconds that your key will expire.
        :type time: int
        :return: True in case of success and False in case of failure
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.set(key, value, time))

        return any(returns)

    def cas(self, key, value, cas, time=0):
        """
        Set a value for a key on server if its CAS value matches cas.

        :param key: Key's name
        :type key: basestring
        :param value: A value to be stored on server.
        :type value: object
        :param time: Time in seconds that your key will expire.
        :type time: int
        :return: True in case of success and False in case of failure
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.cas(key, value, cas, time))

        return any(returns)

    def set_multi(self, mappings, time=0):
        """
        Set multiple keys with it's values on server.

        :param mappings: A dict with keys/values
        :type mappings: dict
        :param time: Time in seconds that your key will expire.
        :type time: int
        :return: True in case of success and False in case of failure
        :rtype: bool
        """
        returns = []
        if mappings:
            for server in self.servers:
                returns.append(server.set_multi(mappings, time))

        return all(returns)

    def add(self, key, value, time=0):
        """
        Add a key/value to server ony if it does not exist.

        :param key: Key's name
        :type key: basestring
        :param value: A value to be stored on server.
        :type value: object
        :param time: Time in seconds that your key will expire.
        :type time: int
        :return: True if key is added False if key already exists
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.add(key, value, time))

        return any(returns)

    def replace(self, key, value, time=0):
        """
        Replace a key/value to server ony if it does exist.

        :param key: Key's name
        :type key: basestring
        :param value: A value to be stored on server.
        :type value: object
        :param time: Time in seconds that your key will expire.
        :type time: int
        :return: True if key is replace False if key does not exists
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.replace(key, value, time))

        return any(returns)

    def delete(self, key, cas=0):
        """
        Delete a key/value from server. If key does not exist, it returns True.

        :param key: Key's name to be deleted
        :type key: basestring
        :return: True in case o success and False in case of failure.
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.delete(key, cas))

        return any(returns)

    def incr(self, key, value):
        """
        Increment a key, if it exists, returns it's actual value, if it don't, return 0.

        :param key: Key's name
        :type key: basestring
        :param value: Number to be incremented
        :type value: int
        :return: Actual value of the key on server
        :rtype: int
        """
        returns = []
        for server in self.servers:
            returns.append(server.incr(key, value))

        return returns[0]

    def decr(self, key, value):
        """
        Decrement a key, if it exists, returns it's actual value, if it don't, return 0.
        Minimum value of decrement return is 0.

        :param key: Key's name
        :type key: basestring
        :param value: Number to be decremented
        :type value: int
        :return: Actual value of the key on server
        :rtype: int
        """
        returns = []
        for server in self.servers:
            returns.append(server.decr(key, value))

        return returns[0]

    def flush_all(self, time=0):
        """
        Send a command to server flush|delete all keys.

        :param time: Time to wait until flush in seconds.
        :type time: int
        :return: True in case of success, False in case of failure
        :rtype: bool
        """
        returns = []
        for server in self.servers:
            returns.append(server.flush_all(time))

        return any(returns)

    def stats(self, key=None):
        """
        Return server stats.

        :param key: Optional if you want status from a key.
        :type key: basestring
        :return: A dict with server stats
        :rtype: dict
        """
        # TODO: Stats with key is not working.

        returns = {}
        for server in self.servers:
            returns[server.server] = server.stats(key)

        return returns

    def disconnect_all(self):
        """
        Disconnect all servers.

        :return: Nothing
        :rtype: None
        """
        for server in self.servers:
            server.disconnect()