import unittest
from unittest import mock

import beanquery


class TestConnection(unittest.TestCase):
    def test_connect_without_source(self):
        for dsn in [None, '']:
            with self.subTest(dsn=dsn):
                connection = beanquery.connect(dsn)
                self.assertEqual(connection.execute('SELECT 42').fetchall(), [(42,)])

    def test_missing_scheme(self):
        connection = beanquery.connect(None)
        for dsn in ['', 'ledger.beancount', './ledger.beancount']:
            with self.subTest(dsn=dsn), self.assertRaisesRegex(beanquery.OperationalError, '^missing source scheme$'):
                connection.attach(dsn)

    def test_connect_missing_scheme(self):
        with self.assertRaisesRegex(beanquery.OperationalError, '^missing source scheme$'):
            beanquery.connect('ledger.beancount')

    def test_unknown_scheme(self):
        for scheme in ['beancounnt', 'unknown', 'foo.bar', 'foo.bar.baz', 'foo+bar', 'foo-bar']:
            with self.subTest(scheme=scheme):
                with self.assertRaises(beanquery.OperationalError) as caught:
                    beanquery.connect(f'{scheme}:ledger')
                self.assertEqual(str(caught.exception), f'unknown source scheme: {scheme!r}')

    def test_message_only_contains_scheme(self):
        with self.assertRaises(beanquery.OperationalError) as caught:
            beanquery.connect('unknown://example.invalid/private-ledger?fixture=synthetic')
        self.assertEqual(str(caught.exception), "unknown source scheme: 'unknown'")

    def test_import_dependency_failure(self):
        names = ['some_dependency', 'beanquery.sources', 'beanquery.sources.other', 'beanquery.sources.foo.optional', None]
        for name in names:
            error = ModuleNotFoundError('missing dependency', name=name)
            with self.subTest(name=name), mock.patch('beanquery.importlib.import_module', side_effect=error):
                with self.assertRaises(ModuleNotFoundError) as caught:
                    beanquery.connect('foo.bar:ledger')
                self.assertIs(caught.exception, error)

    def test_import_error(self):
        error = ImportError('source import failed')
        with mock.patch('beanquery.importlib.import_module', side_effect=error):
            with self.assertRaises(ImportError) as caught:
                beanquery.connect('test:')
            self.assertIs(caught.exception, error)

    def test_source_attach_failure(self):
        error = ModuleNotFoundError('source attach failed', name='beanquery.sources.test')
        source = mock.Mock()
        source.attach.side_effect = error
        with mock.patch('beanquery.importlib.import_module', return_value=source):
            with self.assertRaises(ModuleNotFoundError) as caught:
                beanquery.connect('test:')
            self.assertIs(caught.exception, error)

    def test_source_attach_arguments(self):
        source = mock.Mock()
        dsn = 'test:fixture?name=example'
        entries = []
        options = {'example': 'synthetic'}
        with mock.patch('beanquery.importlib.import_module', return_value=source):
            connection = beanquery.connect(dsn, entries=entries, options=options)
        source.attach.assert_called_once_with(connection, dsn, entries=entries, options=options)

    def test_valid_source(self):
        connection = beanquery.connect('test:magic?name=example&start=1&stop=3')
        self.assertEqual(connection.execute('SELECT x FROM #example').fetchall(), [(1,), (2,)])
