import importlib

from urllib.parse import urlparse

from . import parser
from . import compiler
from . import tables

from .compiler import CompilationError
from .cursor import Cursor, Column
from .errors import Warning, Error, InterfaceError, DatabaseError, DataError, OperationalError
from .errors import IntegrityError, InternalError, ProgrammingError, NotSupportedError
from .parser import ParseError


__version__ = '0.3.0.dev0'


# DB-API compliance
apilevel = '2.0'
threadsafety = 2
paramstyle = 'pyformat'


def connect(dsn, **kwargs):
    return Connection(dsn, **kwargs)


class Connection:
    def __init__(self, dsn='', **kwargs):
        self.tables = {None: tables.NullTable()}

        # The ``None`` table is the default table. The ``''`` table is the
        # table that is explicitly selected with ``FROM #``. Having the
        # default table and the ``''`` table allows to select the empty table
        # when the ``beancount`` data source is initialized and it sets the
        # default table to the ``postings`` table.
        self.tables[''] = self.tables[None]

        # These are used only by the ``beancount`` data source.
        self.options = {}
        self.errors = []

        if dsn:
            self.attach(dsn, **kwargs)

    def attach(self, dsn, **kwargs):
        scheme = urlparse(dsn).scheme
        if not scheme:
            raise OperationalError('missing source scheme')
        source_name = f'beanquery.sources.{scheme}'
        try:
            source = importlib.import_module(source_name)
        except ModuleNotFoundError as exc:
            # Dotted schemes can fail on a missing parent source package.
            # Propagate import failures for other modules.
            missing = exc.name
            missing_source = (
                missing == source_name or
                (missing is not None and missing.startswith('beanquery.sources.') and
                 source_name.startswith(f'{missing}.'))
            )
            if not missing_source:
                raise
            raise OperationalError(f'unknown source scheme: {scheme!r}') from None
        source.attach(self, dsn, **kwargs)

    def close(self):
        # Required by the DB-API.
        pass

    def parse(self, query):
        return parser.parse(query)

    def compile(self, query):
        return compiler.compile(self, query)

    def execute(self, query, params=None):
        return self.cursor().execute(query, params)

    def cursor(self):
        return Cursor(self)


__all__ = [
    'Column',
    'CompilationError',
    'Connection',
    'Cursor',
    'DataError',
    'DatabaseError',
    'Error',
    'IntegrityError',
    'InterfaceError',
    'InternalError',
    'NotSupportedError',
    'OperationalError',
    'ParseError',
    'ProgrammingError',
    'Warning',
    'apilevel',
    'connet',
    'paramstyle',
    'threadsafety',
]
