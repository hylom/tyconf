import unittest
import sys
import os
from typing import Any, Iterable

sys.path.append(os.path.abspath("src"))
from tyconf import TyConf
from tyconf.tyconf import TomlWriter, TyConfKeyError

class TyConfTest(TyConf):
    int_item: int
    str_item: str
    list_of_str_item: list[str]

    def init(self):
        self.add_key("int_item", int, default=0, help="the int value")
        self.add_key("str_item", str, example="hoge", help="the str value")
        self.add_key("list_of_str_item", list[str], example=["foo", "bar"],
                     help="the list value")


class TyConfRequiredTest(TyConf):
    required_item: str

    def init(self):
        self.add_key("required_item", str,
                     required=True,
                     example="hoge", help="the str value")


class TyConfNotRequiredTest(TyConf):
    not_required_item: str

    def init(self):
        self.add_key("not_required_item", str,
                     example="hoge", help="the str value")


@TyConf.conf(ignore_extra=False)
class TyConfTestExtra(TyConf):
    int_item: int
    str_item: str
    list_of_str_item: list[str]

    def init(self):
        self.add_key("int_item", int, default=0, help="the int value")
        self.add_key("str_item", str, example="hoge", help="the str value")
        self.add_key("list_of_str_item", list[str], example=["foo", "bar"],
                     help="the list value")

class TyConfTestParent(TyConf):
    sub_conf: TyConfTest
    int_item: int
    str_item: str
    str_item2: str

    def init(self):
        self.add_key("sub_conf", TyConfTest)
        self.add_key("int_item", int)
        self.add_key("str_item", str)
        self.add_key("str_item2", str)


@TyConf.conf(root=True)
class TyConfTestRoot(TyConf):
    str_item: str

    def init(self):
        self.add_key("str_item", str)


@TyConf.conf(parent="root", name="sub_conf")
class TyConfChild(TyConf):
    int_item: int

    def init(self):
        self.add_key("int_item", int, default=0, help="the int value")


class TestTyConf(unittest.TestCase):
    """Basic test for `TyConf`"""
    def _check_conf_value(self, conf: TyConf, d: dict[str, Any],
                          ignores: Iterable[str] = []):
        ignore_set = set(ignores)
        for k in d:
            if k in ignore_set:
                self.assertFalse(hasattr(conf, k))
                continue
            v = getattr(conf, k)
            if issubclass(v.__class__, TyConf):
                continue
            self.assertEqual(v, d[k], f"invalid value of `{k}`")
        
    def test_direct_use(self):
        "Test using `TyConf` class directly"
        conf = TyConf()
        conf.add_key("int_item", int, default=0, help="the int value")
        conf.add_key("str_item", str, example="hoge", help="the str value")
        conf.add_key("list_of_str_item", list[str], example=["foo", "bar"],
                     help="the list value")
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ]
        }
        result = conf.parse_dict(d)
        for k in d:
            self.assertEqual(result[k], d[k])

    def test_parse_valid_dict(self):
        "Check functionality for non-recursive dictionary"
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ]
        }
        conf = TyConfTest()
        conf.parse_dict(d)
        self._check_conf_value(conf, d)

    def test_mutable_mapping(self):
        "Check functionality of TyConf as MutableMapping"
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ]
        }
        conf = TyConfTest()
        conf.parse_dict(d)
        conf["int_item"] = 2
        del conf["str_item"]
        self.assertEqual(2, conf.int_item)
        with self.assertRaises(AttributeError) as cm:
            conf.str_item

    def test_undefined_key(self):
        "Check functionality when the dictionary has undefined keys"
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ],
            "other1": True,
            "other2": ""
        }
        conf = TyConfTest()
        conf.parse_dict(d)
        self._check_conf_value(conf, d, ignores=("other1", "other2"))

    def test_required_key(self):
        "Check functionality of required key"
        d = {}
        conf = TyConfRequiredTest()
        with self.assertRaises(TyConfKeyError) as cm:
            conf.parse_dict(d)

    def test_not_required_key(self):
        "Check functionality of not-required key"
        d = {}
        conf = TyConfNotRequiredTest()
        conf.parse_dict(d)

    def test_ignore_extra_false(self):
        "Check functionality when the dictionary has undefined keys and ignore_extra is True"
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ],
            "other1": True,
            "other2": ""
        }
        conf = TyConfTestExtra()
        conf.parse_dict(d)
        self._check_conf_value(conf, d)

    def test_recursive_dict(self):
        "Check functionality for the recursive dictionary"
        d = {
            "int_item": 2,
            "str_item": "moge",
            "str_item2": "hoge",
            "sub_conf": {
                "int_item": 1,
                "str_item": "hoge",
                "list_of_str_item": [ "foo", "bar", "baz" ]
            }
        }
        conf = TyConfTestParent()
        conf.parse_dict(d)
        self._check_conf_value(conf, d)

    def test_parent_decorator(self):
        "Check decorator with parent argument functionality "
        d = {
            "str_item": "hoge",
            "sub_conf": {
                "int_item": 1,
            }
        }
        conf = TyConfTestRoot()
        conf.parse_dict(d)
        self._check_conf_value(conf, d)

    def test_key_and_iterator_access(self):
        "Check [] style access"
        d = {
            "int_item": 1,
            "str_item": "hoge",
            "list_of_str_item": [ "foo", "bar", "baz" ]
        }
        conf = TyConfTest()
        conf.parse_dict(d)
        for k in d:
            self.assertEqual(conf[k], d[k])
        for k in conf:
            self.assertEqual(conf[k], d[k])

class TestTomlWriter(unittest.TestCase):
    """ Basic test for TomlWriter"""
    def test_dumps(self):
        "Check TomlWriter.dumps()"
        conf = TyConfTest()
        writer = TomlWriter()
        s = writer.dumps(conf)
        expected = """\
## int_item (int): the int value.
## Default: 0
int_item = 0

## str_item (str): the str value.
# str_item = "hoge"

## list_of_str_item (list): the list value.
# list_of_str_item = ['foo', 'bar']
"""
        self.assertEqual(s, expected)

    def test_dumps_with_nested(self):
        "Check TomlWriter.dumps() with nested `TyConf`"
        conf = TyConfTestParent()
        writer = TomlWriter()
        s = writer.dumps(conf)
        expected = """\
## int_item (int):
# int_item = 

## str_item (str):
# str_item = 

## str_item2 (str):
# str_item2 = 

[sub_conf]
## int_item (int): the int value.
## Default: 0
int_item = 0

## str_item (str): the str value.
# str_item = "hoge"

## list_of_str_item (list): the list value.
# list_of_str_item = ['foo', 'bar']

"""
        self.assertEqual(s, expected)

    def test_dumps_with_parent(self):
        "Check TomlWriter.dumps() with `TyConf` subclass with conf(parent=...)"
        conf = TyConfTestRoot()
        writer = TomlWriter()
        s = writer.dumps(conf)
        expected = """\
## str_item (str):
# str_item = 

[sub_conf]
## int_item (int): the int value.
## Default: 0
int_item = 0

"""
        self.assertEqual(s, expected)


if __name__ == '__main__':
    unittest.main()
