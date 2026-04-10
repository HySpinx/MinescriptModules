"""
    @author RazrCraft
    @create date 2025-09-18 23:31:14
    @modify date 2025-09-23 14:35:05
    @desc Simple JSON-backed configuration library
"""

from __future__ import annotations
import json
import os
import tempfile
from typing import Any, Dict


class ConfigError(Exception):
    """Generic configuration error."""


def _is_json_serializable(value: Any) -> bool:
    """Return True if value is JSON-serializable by the standard json module."""
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False


class ConfigNode:
    """
    Wrapper that provides attribute-style access to a nested dictionary.

    Example:
        root = ConfigNode(config, [])
        root.section.sub = 123
        value = root.section.sub
    """
    __slots__ = ("_config", "_path")

    def __init__(self, config: "Config", path: list[str]):
        # _config: reference to top-level Config instance
        # _path: list of keys from root to this node
        object.__setattr__(self, "_config", config)
        object.__setattr__(self, "_path", path)

    def _get_target(self):
        """Return the container (dict) and final key for this node's path."""
        d = self._config._data
        if not self._path:
            return d, None
        for key in self._path[:-1]:
            d = d.setdefault(key, {})
            if not isinstance(d, dict):
                # If encountering non-dict while traversing, replace with dict
                # to allow nested assignment.
                d_parent = self._config._data
                for k in self._path[: self._path.index(key)]:
                    d_parent = d_parent[k]
                d_parent[key] = {}
                d = d_parent[key]
        return d, self._path[-1]

    # Attribute access
    def __getattr__(self, name: str) -> Any:
        # called when name not found on instance; treat as key lookup
        if name.startswith("_"):
            raise AttributeError(name)
        d = self._config._data
        for key in self._path:
            d = d.get(key, {})
            if not isinstance(d, dict):
                # If this intermediate path is not a dict, then no attributes available
                break
        if not isinstance(d, dict):
            # d is a value -> attribute access not allowed
            raise AttributeError(f"'{name}' not found because path is a value")
        if name not in d:
            # return a node for further nested access (creates lazily)
            return ConfigNode(self._config, self._path + [name])
        val = d[name]
        if isinstance(val, dict):
            return ConfigNode(self._config, self._path + [name])
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        if not _is_json_serializable(value):
            raise ConfigError("Value is not JSON-serializable")
        container, final_key = self._get_target()
        # Ensure intermediate container is a dict
        if final_key is not None:
            # Move into nested dict
            container = container.setdefault(final_key, {})
            if not isinstance(container, dict):
                # Overwrite non-dict with dict to store nested attribute
                parent, fk = self._get_target_for_parent()
                parent[fk] = {}
                container = parent[fk]
        container[name] = value
        if self._config._autosave:
            self._config.save()

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            raise AttributeError(name)
        d = self._config._data
        for key in self._path:
            d = d.get(key, {})
            if not isinstance(d, dict):
                break
        if not isinstance(d, dict) or name not in d:
            raise AttributeError(name)
        del d[name]
        if self._config._autosave:
            self._config.save()

    def __getitem__(self, key: str) -> Any:
        # dictionary-style access: node['key']
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def _get_target_for_parent(self):
        """
        Helper: return (parent_dict, final_key) where parent_dict[final_key] is
        the dict representing this node.
        """
        if not self._path:
            return self._config._data, None
        d = self._config._data
        for key in self._path[:-1]:
            d = d.setdefault(key, {})
            if not isinstance(d, dict):
                # Fix non-dict intermediate
                d_parent = self._config._data
                for k in self._path[: self._path.index(key)]:
                    d_parent = d_parent[k]
                d_parent[key] = {}
                d = d_parent[key]
        return d, self._path[-1]

    def to_dict(self) -> dict:
        """Return a plain dict view of this node."""
        d = self._config._data
        for key in self._path:
            d = d.get(key, {})
        if isinstance(d, dict):
            return json.loads(json.dumps(d))
        return d

    def __repr__(self):
        return f"<ConfigNode path={'.'.join(self._path) if self._path else '<root>'}>"


class Config:
    """
    JSON-backed configuration object.

    Example:
        config = Config("settings.json", autosave=True)
        config.database.host = "localhost"
        config.database.port = 3306
        print(config.database.host)
        config.save()  # if autosave=False
    """

    def __init__(self, path: str, autosave: bool = True):
        self._path = os.fspath(path)
        self._autosave = bool(autosave)
        self._data: Dict[str, Any] = {}
        self._load_or_create()

    def _load_or_create(self) -> None:
        if not os.path.exists(self._path):
            parent = os.path.dirname(self._path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._data = {}
            self.save()
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            if not isinstance(self._data, dict):
                raise ConfigError("Top-level JSON must be an object/dictionary")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config file: {e}") from e
        except OSError as e:
            raise ConfigError(f"Error reading config file: {e}") from e

    def save(self) -> None:
        """Atomically write current configuration to disk."""
        dirpath = os.path.dirname(self._path) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_config_", dir=dirpath)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                json.dump(self._data, tmpf, ensure_ascii=False, indent=2)
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_path, self._path)
        except OSError as e:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise ConfigError(f"Error saving config file: {e}") from e

    def reload(self) -> None:
        self._load_or_create()

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._data))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._data and not isinstance(self._data[name], dict):
            return self._data[name]
        return ConfigNode(self, [name])

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        if not _is_json_serializable(value):
            raise ConfigError("Value is not JSON-serializable")
        self._data[name] = value
        if self._autosave:
            self.save()

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._data:
            raise AttributeError(name)
        del self._data[name]
        if self._autosave:
            self.save()

    def __getitem__(self, key: str) -> Any:
        if key in self._data and not isinstance(self._data[key], dict):
            return self._data[key]
        return ConfigNode(self, [key])

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __enter__(self) -> "Config":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._autosave:
            self.save()

    def __repr__(self):
        return f"<Config path={self._path!r} autosave={self._autosave}>"
