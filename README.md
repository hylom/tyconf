# tyconf - configuration-file parser with type-checking

## What is this?

`tyconf` is a Python library to check configuration file, inspired by `argparse`. This provides `TyConf` class that is a container for configuration key specifications.

## How to use

### Direct use of `TyConf` class

At first, import `tyconf` and create `TyConf` instance.

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

An return value of the `parse_dict()` is a `dict` contains parsed values. Also an instance of `TyConf` itself contains parsed values:

```python
>>> conf["int_item"]
1
>>> conf["str_item"]
'hoge'
>>> conf["list_of_str_item"]
['foo', 'bar', 'baz']

```

By default, only defined key with `add_key()` method will be parsed and included in result of the `parse_dict()` method. For example, `undefined_item` exists in a `dict` given to `parse_dict()` method, but the both the `TyConf` instance and `dict` returned from `parse_dict()` do not contain `undefined_item`.

```python
>>> conf["undefined_item"]
Traceback (most recent call last):
    ...
KeyError: 'undefined_item'

```

To include undefined key, use `ignore_extra` parameter:

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

### Use with subclass

We recommend using `TyConf` with creating subclass:

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

An instance of `TyConf` subclass contains parsed values:

```python
>>> conf["int_item"]
1
>>> conf["str_item"]
'hoge'
>>> conf["list_of_str_item"]
['foo', 'bar', 'baz']

```

### Generate skelton TOML format configuration file

You can generate skelton configuration file in TOML format with `TomlWriter`:

```
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

