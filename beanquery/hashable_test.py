import dataclasses
import unittest

from beanquery import hashable
from beanquery.cursor import Column


class TestHashable(unittest.TestCase):

    def test_fundamental(self):
        columns = (Column('b', bool), Column('i', int), Column('s', str))
        wrap = hashable.make(columns)
        obj = (True, 42, 'universe')
        self.assertIs(wrap(obj), obj)
        hash(obj)

    def test_dict(self):
        columns = (Column('b', bool), Column('d', dict))
        wrap = hashable.make(columns)
        obja = (True, {'answer': 42})
        a = hash(wrap(obja))
        objb = (True, {'answer': 42})
        b = hash(wrap(objb))
        self.assertIsNot(obja, objb)
        self.assertEqual(a, b)
        objc = (False, {'answer': 42})
        c = hash(wrap(objc))
        self.assertNotEqual(a, c)
        objd = (True, {'answer': 43})
        d = hash(wrap(objd))
        self.assertNotEqual(a, d)

    def test_set(self):
        wrap = hashable.make((Column('tags', set),))
        for obj in ((frozenset(),), (frozenset({'one', 'two'}),)):
            with self.subTest(obj=obj):
                self.assertEqual(wrap(obj), obj)
                self.assertEqual(hash(wrap(obj)), hash(obj))

    def test_set_iteration_order(self):
        wrap = hashable.make((Column('flag', bool), Column('tags', set)))
        first = (0, 8)
        second = (8, 0)
        a = wrap((True, set(first)))
        b = wrap((True, set(second)))
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_dict_insertion_order(self):
        wrap = hashable.make((Column('meta', dict),))
        a = wrap(({'one': 1, 'two': 2},))
        b = wrap(({'two': 2, 'one': 1},))
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)
        self.assertNotEqual(a, wrap(({'one': 2, 'two': 1},)))

    def test_nullable_containers(self):
        for dtype in (set, dict):
            with self.subTest(dtype=dtype):
                wrap = hashable.make((Column('value', dtype),))
                self.assertEqual(wrap((None,)), (None,))
                self.assertEqual(hash(wrap((None,))), hash((None,)))
                self.assertNotEqual(wrap((None,)), wrap((dtype(),)))

    def test_set_with_other_columns(self):
        wrap = hashable.make((Column('flag', bool), Column('tags', set)))
        obj = (True, frozenset({'one', 'two'}))
        self.assertEqual(wrap(obj), obj)
        self.assertEqual(hash(wrap(obj)), hash(obj))

    def test_registered(self):

        @dataclasses.dataclass
        class Foo:
            xid: int
            meta: dict

        hashable.register(Foo, lambda obj: obj.xid)

        columns = (Column('b', bool), Column('foo', Foo))
        wrap = hashable.make(columns)
        obja = (True, Foo(1, {'test': 1}))
        a = hash(wrap(obja))
        objb = (True, Foo(1, {'test': 2}))
        b = hash(wrap(objb))
        self.assertEqual(a, b)
        objc = (True, Foo(2, {'test': 2}))
        c = hash(wrap(objc))
        self.assertNotEqual(a, c)
