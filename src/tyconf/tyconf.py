from __future__ import annotations

__version__ = "0.1"
__all__ = [ "TyConf" ]

from types import GenericAlias
from typing import Any, Callable, ClassVar, IO, TypeVar
from pathlib import Path
from datetime import datetime, date, time
import json
import tomllib
from collections.abc import MutableMapping, Iterator


import logging
logger = logging.getLogger(__name__)

_RootConf: type | None = None

class ParseError(Exception):
    pass

class TyConfKeyError(Exception):
    pass


class TyConfKey[T]:
    """Typed configuration key object"""
    name: str
    type: T
    action: str
    default: T | None
    example: T | None
    choises: list[T] | None
    required: bool
    help: str
    metavar: str
    deprecated: bool
    value: T | None

    def __init__(self, 
                   name: str,
                   type: T,
                   action: str = "store",
                   default: T | None = None,
                   example: T | None = None,
                   choises: list[T] | None = None,
                   required: bool = False,
                   help: str = "",
                   metavar: str = "",
                   deprecated: bool = False,
                   ):
        if not name:
            msg = "key name is not given"
            raise TyConfKeyError(msg)
        if not type:
            msg = "type is not given"
            raise TyConfKeyError(msg)
        if not metavar:
            metavar = name.upper()

        self.name = name
        self.type = type
        self.action = action
        self.default = default
        self.example = example
        self.choises = choises
        self.required = required
        self.help = help
        self.metavar = metavar
        self.deprecated = deprecated
        self.value = None

    def gen_doc_text(self, multi_line=False):
        t: list[str] = []
        if self.required:
            base_text = f"""{self.name} ({self.type.__name__}, required):"""
        else:
            base_text = f"""{self.name} ({self.type.__name__}):"""
        t.append(base_text)
        if self.help:
            t.append(f""" {self.help}.""")
        if self.deprecated:
            t.append(" (deprecated)")
        if self.default is not None:
            if multi_line:
                t.append("\n")
            else:
                t.append(" ")
            if isinstance(self.default, str):
                t.append(f'''Default: "{self.default}"''')
            else:
                t.append(f"""Default: {self.default}""")
        return "".join(t)

class TyConf(MutableMapping):
    """Typed configuration parser inspired from `argparse`"""
    ignore_extra: ClassVar[bool] = True
    init_func: ClassVar[str] = "init"
    children: ClassVar[dict[str, type]] = {}
    _conf_keys: list[TyConfKey]
    _conf_items: dict[str, object]

    @classmethod
    def conf[F: Callable[..., Any]](cls,
                                    ignore_extra: bool = True,
                                    root: bool = False,
                                    parent: str | type = "",
                                    name: str = "",
                                    init: str = "init",
                                    ) -> Callable[[F], F]:
        def wrapper(target_cls):
            global _RootConf
            if root:
                _RootConf = target_cls
                # need to set new dict not to share the dict of root (`TyConf`)
                target_cls.children = {}
            if parent:
                if isinstance(parent, str):
                    if parent == "root":
                        P = _RootConf
                    else:
                        raise KeyError(f"parent must be `root`, but {parent} is given")
                else:
                    P = parent
                if name:
                    P.children[name] = target_cls
                else:
                    raise KeyError(f"`name` is required when `parent` is given")
            target_cls.ignore_extra = ignore_extra
            target_cls.init_func = init
            return target_cls
        return wrapper

    def __init__(self, init_args={}, /, ignore_extra: bool | None = None):
        self._conf_keys = []
        self._conf_items = {}
        if ignore_extra is not None:
            self.ignore_extra = ignore_extra
        # call init func
        fn = getattr(self, self.init_func)
        fn()

        # append children
        for name, T in self.children.items():
            self.add_key(name, T)

        if init_args:
            self.parse_dict(init_args)

    def _get_name(self) -> str:
        return self.__class__.__name__

    def init(self) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        try:
            return self._conf_items[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key: str) -> Any:
        return self._conf_items[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._conf_items[key] = value

    def __delitem__(self, key: str) -> None:
        del self._conf_items[key]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._conf_items)

    def __len__(self) -> int:
        return len(self.__dict__)

    def add_key[T](self,
                   name: str,
                   type: T,
                   action: str = "store",
                   default: T | None = None,
                   example: T | None = None,
                   choises: list[T] | None = None,
                   required: bool = False,
                   help: str = "",
                   metavar: str = "",
                   deprecated: bool = False,
                   ):
        k = TyConfKey(name, type, action, default, example, choises,
                      required, help, metavar, deprecated)
        self._conf_keys.append(k)

    def parse_dict(self, d: dict[str, Any]) -> dict[str, object]:
        d_keys = set(d.keys())
        for key in self._conf_keys:
            self._set_value(key.name, self._check_key(key, d))
            try:
                d_keys.remove(key.name)
            except KeyError:
                pass

        # set undefined values
        if d_keys:
            if self.ignore_extra:
                ks = ", ".join([f"`{x}`" for x in d_keys])
                msg = f"undefined keys found and ignored: {ks}"
                logger.debug(msg)
            else:
                for key in d_keys:
                    self._set_value(key, d[key])
        return self._dict()

    def parse_file(self, filename: str, format: str = ""):
        path = Path(filename)
        if not format:
            if not path.suffix:
                msg = f"cannot determine file format: {filename}"
                raise ParseError(msg)
            format = path.suffix[1:].lower()
        if format == "json":
            self._parse_json(path)
        elif format == "toml":
            self._parse_toml(path)
        else:
            msg = f"file format `{format}` is not supported"
            raise ParseError(msg)

    def _parse_json(self, path: Path):
        with path.open() as fp:
            d = json.load(fp)
        self.parse_dict(d)

    def _parse_toml(self, path: Path):
        with path.open("rb") as fp:
            d = tomllib.load(fp)
        self.parse_dict(d)

    def _set_value(self, key: str, value: Any):
        self._conf_items[key] = value

    def _dict(self) -> dict[str, object]:
        return self._conf_items

    def _check_key(self, key: TyConfKey, d: dict[str, Any]) -> object:
        try:
            val = d[key.name]
        except KeyError:
            if key.required:
                msg = f"Required key `{key.name}` does not exist"
                raise TyConfKeyError(msg)
            return None
        if isinstance(key.type, GenericAlias):
            key_type: type = key.type.__origin__
        else:
            key_type: type = key.type
        if not isinstance(val, key_type):
            val = self._convert_value(val, key, key_type)
        return val

    def _convert_value(self, value: object, key: TyConfKey, key_type: type):
        T = key_type
        try:
            return T(value)
        except ValueError:
            dest_type = T.__name__
            msg = f"Failed to parse {value} (key: {key.name}) as {dest_type}"
            raise TyConfKeyError(msg)
        except Exception as e:
            dest_type = T.__name__
            msg = f"Failed to parse {value} (key: {key.name}) as {dest_type}: {e}"
            raise TyConfKeyError(msg)

    def __repr__(self):
        return f"<{self.__class__.__name__} object: {str(self._dict())}"
        

class TomlWriter:
    """Generate initial configuration toml file from `TyConf`"""
    native_type: ClassVar[list[type]] = [dict, str, int, float, bool,
                                         datetime, date, time, list]

    def _is_native_type(self, t: type) -> bool:
        if isinstance(t, GenericAlias):
            t = t.__origin__
        return t in self.native_type
        
    def _dump_line(self, key: TyConfKey) -> str:
        comment = True
        if key.default is not None:
            val = key.default
            comment = False
        elif key.example:
            val = key.example
        else:
            val = None
        if isinstance(val, str):
            val = f'"{val}"'
        elif isinstance(val, bool):
            if val:
                val = "true"
            else:
                val = "false"
        # TODO: need to handle dict correctly
        elif isinstance(val, datetime):
            val = val.isoformat()
        if val is not None:
            if comment:
                return f"""# {key.name} = {val}"""
            else:
                return f"""{key.name} = {val}"""
        return f"""# {key.name} = """

    def dump(self, fp: IO[str], conf: TyConf):
        fp.write(self.dumps(conf))
        
    def dumps(self, conf: TyConf) -> str:
        result: list[str] = []
        sub_confs: list[TyConfKey] = []
        for k in conf._conf_keys:
            if self._is_native_type(k.type):
                doc = k.gen_doc_text(multi_line=True)
                for l in doc.split("\n"):
                    result.append(f"""## {l}""")
                result.append(self._dump_line(k))
                result.append("") # insert blank line
            elif issubclass(k.type, TyConf):
                sub_confs.append(k)
                continue
        for k in sub_confs:
            if k.help:
                help_msg = k.help
            else:
                help_msg = k.type.__doc__
            if help_msg:
                result.append(f"""## {help_msg}""")
            result.append(f"""[{k.name}]""")
            T = k.type
            v = T()
            result.append(self.dumps(v))
            result.append("") # insert blank line

        return "\n".join(result)
                

