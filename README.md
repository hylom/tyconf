# tyconf - configuration file parser with type-checking

## What is this?

`tyconf` is a Python library to check configuration files, inspired by `argparse`. This provides the `TyConf` class that parse configuration file. This class also serves as a container that holds combinations of configuration keys and their values.

## How to use

### Direct use of `TyConf` class

First, import `tyconf` and create `TyConf` instance.

```python
>>> from tyconf import TyConf
>>> conf = TyConf()

```

You can add configuration key using the `add_key` method:

```python
>>> conf.add_key("int_item", int, default=0, help="the int value")
>>> conf.add_key("str_item", str, example="hoge", help="the str value")
>>> conf.add_key("list_of_str_item", list[str], example=["foo", "bar"],
...             help="the list value")

```

And you can parse dict-like object using `parse_dict()` method: 

```python
>>> d = {
...    "int_item": 1,
...    "str_item": "hoge",
...    "list_of_str_item": [ "foo", "bar", "baz" ],
...    "undefined_item": "This is extra value",
... }
>>> conf.parse_dict(d)
{'int_item': 1, 'str_item': 'hoge', 'list_of_str_item': ['foo', 'bar', 'baz']}

```

The return value of the `parse_dict()` is a `dict` containing parsed values. Also an instance of `TyConf` itself contains parsed values:

```python
>>> conf["int_item"]
1
>>> conf["str_item"]
'hoge'
>>> conf["list_of_str_item"]
['foo', 'bar', 'baz']

```

By default, only defined key with `add_key()` method will be parsed and included in result of the `parse_dict()` method. For example, `undefined_item` exists in a `dict` given to `parse_dict()` method, neither the `TyConf` instance nor the `dict` returned from `parse_dict()` contains `undefined_item`.

```python
>>> conf["undefined_item"]
Traceback (most recent call last):
    ...
KeyError: 'undefined_item'

```

To include undefined keys, use `ignore_extra` parameter:

```python
>>> conf = TyConf(ignore_extra=False)

>>> conf.add_key("int_item", int, default=0, help="the int value")
>>> conf.add_key("str_item", str, example="hoge", help="the str value")
>>> conf.add_key("list_of_str_item", list[str], example=["foo", "bar"],
...             help="the list value")

>>> d = {
...    "int_item": 1,
...    "str_item": "hoge",
...    "list_of_str_item": [ "foo", "bar", "baz" ],
...    "undefined_item": "This is extra value",
... }

>>> conf.parse_dict(d)
{'int_item': 1, 'str_item': 'hoge', 'list_of_str_item': ['foo', 'bar', 'baz'], 'undefined_item': 'This is extra value'}

```

### Type conversion

If the type of the value provided during parsing differs from the type specified by `type` of the key, automatic type conversion is performed. If type conversion fails, an exception is raised.

For example, `"1"` (of type `str`) can be automatically converted to `1` (of type `int`).

```python
>>> conf = TyConf()
>>> conf.add_key("int_item", int, default=0, help="the int value")
>>> d = {
...    "int_item": "1",
... }
>>> conf.parse_dict(d)
{'int_item': 1}

```

### Use with subclass

We recommend using `TyConf` with creating subclass. The subclass of the `TyConf` executes `init()` method (not `__init__()` method!) in the constructor. Therefore, you can define configuration keys by calling the `add_key()` method within this method like this:

```python
>>> class TyConfTest(TyConf):
...     int_item: int
...     str_item: str
...     list_of_str_item: list[str]
... 
...     def init(self):
...         self.add_key("int_item", int, default=0, help="the int value")
...         self.add_key("str_item", str, example="hoge", help="the str value")
...         self.add_key("list_of_str_item", list[str], example=["foo", "bar"],
...                      help="the list value")

```


```python
>>> conf = TyConfTest()
>>> d = {
...     "int_item": 1,
...     "str_item": "hoge",
...     "list_of_str_item": [ "foo", "bar", "baz" ]
... }
>>> conf.parse_dict(d)
{'int_item': 1, 'str_item': 'hoge', 'list_of_str_item': ['foo', 'bar', 'baz']}

```

An instance of a `TyConf` subclass contains parsed values. You can access these values via both indexs-style (`[key]` format) and attribute-style (`.key` format):

```python
>>> conf["int_item"]
1
>>> conf.int_item
1
>>> conf["str_item"]
'hoge'
>>> conf.str_item
'hoge'
>>> conf["list_of_str_item"]
['foo', 'bar', 'baz']
>>> conf.list_of_str_item
['foo', 'bar', 'baz']

```

Attribute-style access is useful when using static typing.

### Nested configuration

 You can give subclass of the `TyConf` class as a type of the configuration key:
 
```python
>>> class TyConfTest(TyConf):
...     str_item: str
... 
...     def init(self):
...         self.add_key("str_item", str, example="hoge", help="the str value")

>>> class TyConfTestParent(TyConf):
...     sub_conf: TyConfTest
...     int_item: int
... 
...     def init(self):
...         self.add_key("sub_conf", TyConfTest)
...         self.add_key("int_item", int)

```

```python
>>> d = {
...     "int_item": 1,
...     "sub_conf": {
...         "str_item": "bar",
...     }
... }


>>> conf = TyConfTestParent()
>>> conf.parse_dict(d)
{'sub_conf': <TyConfTest object: {'str_item': 'bar'}, 'int_item': 1}

```


### `@TyConf.conf` decorator

You can customize the behavior of subclass of the`TyConf` class using `@TyConf.conf` decorator.

For example, to use `ignore_extra=False` parameter by default, add the `@TyConf.conf(ignore_extra=False)` decorator to the class declaration:

```python
>>> @TyConf.conf(ignore_extra=False)
... class TyConfTestExtra(TyConf):
...     int_item: int
...     str_item: str
...     list_of_str_item: list[str]
... 
...     def init(self):
...         self.add_key("int_item", int, default=0, help="the int value")
...         self.add_key("str_item", str, example="hoge", help="the str value")
...         self.add_key("list_of_str_item", list[str], example=["foo", "bar"],
...                      help="the list value")

```

```python
>>> d = {
...    "int_item": 1,
...    "str_item": "hoge",
...    "list_of_str_item": [ "foo", "bar", "baz" ],
...    "undefined_item": "This is extra value",
... }

>>> conf = TyConfTestExtra()
>>> conf.parse_dict(d)
{'int_item': 1, 'str_item': 'hoge', 'list_of_str_item': ['foo', 'bar', 'baz'], 'undefined_item': 'This is extra value'}

```

### Nested configuration with `@TyConf.conf` decorator

You can define parent-child relationships between `TyConf` subclasses using the `@TyConf.conf()` classmethod decorator. This is useful for hierarchical configuration files.

```python
@TyConf.conf(root=True)
class RootConfig(TyConf):
    str_item: str

    def init(self):
        self.add_key("str_item", str, help="the str value")


@TyConf.conf(parent="root", name="sub_conf")
class SubConfig(TyConf):
    int_item: int

    def init(self):
        self.add_key("int_item", int, default=0, help="the int value")


conf = RootConfig()
d = {
    "str_item": "hoge",
    "sub_conf": {"int_item": 1},
}
conf.parse_dict(d)
```

### Parse configuration from file

You can also parse configuration files in JSON or TOML format using `parse_file()` method. The file format is auto-detected from the file extension (`.json` or `.toml`).

```python
conf = TyConfTest()
conf.parse_file("config.toml")

conf = TyConfTest()
conf.parse_file("config.json")
```

### Generate a skeleton TOML configuration file

You can generate a skeleton TOML configuration file with the `TomlWriter` class:

```python
>>> from tyconf import TomlWriter
>>> class TyConfTest(TyConf):
...     int_item: int
...     str_item: str
...     list_of_str_item: list[str]
... 
...     def init(self):
...         self.add_key("int_item", int, default=0, help="the int value")
...         self.add_key("str_item", str, example="hoge", help="the str value")
...         self.add_key("list_of_str_item", list[str], example=["foo", "bar"],
...                      help="the list value")

>>> conf = TyConfTest()
>>> writer = TomlWriter()

>>> print(writer.dumps(conf))
## int_item (int): the int value.
## Default: 0
int_item = 0
<BLANKLINE>
## str_item (str): the str value.
# str_item = "hoge"
<BLANKLINE>
## list_of_str_item (list): the list value.
# list_of_str_item = ['foo', 'bar']
<BLANKLINE>

```

## API Reference

### `TyConf` class

A typed configuration parser container inspired by `argparse`. Supports dictionary-style access and iteration over configured keys.

#### Constructor

```python
TyConf(init_args: dict = {}, /, ignore_extra: bool | None = None)
```

 - `init_args`: Optional dict to parse immediately on construction.
 - `ignore_extra`: Override the class-level `ignore_extra` setting for this instance. Pass `None` to use the class default.

#### Methods

##### `add_key(name: str, type: T, action: str = "store", default: T | None = None, example: T | None = None, choises: list[T] | None = None, required: bool = False, help: str = "", metavar: str = "", deprecated: bool = False) -> None`

Register a typed configuration key. Supported `type` values include built-in types (`int`, `str`, `bool`, `float`) and generic aliases like `list[str]`.

##### `parse_dict(d: dict[str, Any]) -> dict[str, object]`

Parse a dictionary-like object. Returns a dict of validated and converted values. The parsed values are also stored on the instance and accessible via indexing (`conf["key"]`) and iteration.

##### `parse_file(filename: str, format: str = "") -> None`

  Parse a configuration file. Supported formats are `json` and `toml`. The format is auto-detected from the file extension if `format` is not specified.

##### `@TyConf.conf()` decorator (classmethod)

Configure subclass behavior:

```python
@TyConf.conf(ignore_extra=True, root=False, parent="", name="", init="init")
```

 - `ignore_extra`: Set class-level `ignore_extra` for the decorated class.
 - `root`: Mark the class as the root config when defining nested hierarchies.
 - `parent`: Set the parent class. Use `"root"` to reference the class decorated with `root=True`.
 - `name`: Name of this config as a child of its parent. Required when `parent` is set.
 - `init`: Name of the initialization method.

### `TomlWriter` class

Generate skeleton TOML configuration files from `TyConf` instances.

#### Constructor

```python
TomlWriter()
```

#### Methods

##### `dumps(conf: TyConf) -> str`

Return a TOML string representation of the configuration. Keys with `default` values are written as active settings; keys with only `example` values are written as commented-out examples. Nested `TyConf` subclasses are written as TOML tables.

##### `dump(fp: IO[str], conf: TyConf) -> None`

Write the TOML output to a file-like object.

Built-in types (`dict`, `str`, `int`, `float`, `bool`, `datetime`, `date`, `time`, `list`) are rendered directly. Nested `TyConf` subclasses produce TOML tables. Other classes are rendered as `str`.

#### Exceptions

- `ParseError`: Raised when a file format cannot be determined or is unsupported.
- `TyConfKeyError`: Raised when type conversion fails or a required key is missing.

## Running tests

Unit tests are located in the `tests` directory:

- `tests/test_tyconf.py` - Comprehensive unit tests for `TyConf` and `TomlWriter`
- `tests/test_doctest.py` - Doctests from the `README.md`

Run all tests with `unittest`:

```bash
$ python -m unittest discover -s tests -v
```

Or run a specific test file:

```bash
$ python -m unittest tests.test_tyconf -v
$ python -m unittest tests.test_doctest -v
```
