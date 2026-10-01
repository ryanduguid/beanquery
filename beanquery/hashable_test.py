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
        for value, expected in [
                (None, None),
                (set(), frozenset()),
                (frozenset(), frozenset()),
                ({1, 2}, frozenset({1, 2})),
                (frozenset({1, 2}), frozenset({1, 2}))]:
            with self.subTest(value=value):
                wrapped = wrap((value,))
                self.assertEqual(wrapped, (value,))
                self.assertIs(wrapped[0], value)
                self.assertEqual(hash(wrapped), hash((expected,)))

    def test_set_iteration_order(self):
        class OrderedSet(set):
            def __init__(self, values, reverse=False):
                super().__init__(values)
                self.reverse = reverse

            def __iter__(self):
                return iter(sorted(set.__iter__(self), reverse=self.reverse))

        wrap = hashable.make((Column('flag', bool), Column('tags', set)))
        first = wrap((True, OrderedSet([1, 2, 3])))
        second = wrap((True, OrderedSet([1, 2, 3], reverse=True)))
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(len({first, second}), 1)

    def test_multiple_sets(self):
        wrap = hashable.make((Column('tags', set), Column('links', set)))
        for values, expected in [
                (({1, 2}, {3, 4}), (frozenset({1, 2}), frozenset({3, 4}))),
                ((set(), {1, 2}), (frozenset(), frozenset({1, 2}))),
                ((None, set()), (None, frozenset()))]:
            with self.subTest(values=values):
                self.assertEqual(hash(wrap(values)), hash(expected))

    def test_nullable_set(self):
        wrap = hashable.make((Column('flag', bool), Column('tags', set)))
        rows = [wrap((True, None)), wrap((True, set())), wrap((True, None)), wrap((True, frozenset()))]
        self.assertEqual(len(set(rows)), 2)
        self.assertEqual(rows[1], rows[3])
        self.assertEqual(hash(rows[1]), hash(rows[3]))

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
