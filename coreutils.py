"""
This module provides a fluent interface of Unix-inspired utilities
like 'cut', 'sort', etc, that can be chained together to implement
complex data transformations with very little code.

Because the fundamental chaining objects are all iterators, this
module can cooperate seamlessly in all types of comprehensions,
for-loops and functions expecting iterators.  The IterReader class
also enables the consumption of record streams originating from
other modules or sources.
"""

import re
import sys


# verbose is used to cleanly enable or silence all .count(), .show()
# and .head() operations

_verbose = True
_zero_based = False


def set_verbose(verbose):
    """Turn head() and show() on or off globally."""
    global _verbose

    _verbose = True if verbose else False


def get_verbose():
    """Get the global verbose setting."""
    global _verbose
    return _verbose


def set_zero_based(zero_based):
    """Set whether fields start at 0 or 1."""
    global _zero_based

    _zero_based = True if zero_based else False


def get_zero_based():
    """Get zero_based setting."""
    global _zero_based
    return _zero_based


def flatten(list_of_lists):
    """Return a list-of-lists into a single list with only items in it."""
    return [item for inner_list in list_of_lists for item in inner_list]


def writeln(msg):
    """Console output function to avoid reliance on built-in print."""
    if isinstance(msg, str):
        sys.stdout.write(msg)
    else:
        sys.stdout.write(str(msg))

    sys.stdout.write('\n')


class Cond(object):
    """Callable class that generates a function that can be used with filter()

    The canonical use is:

        Cond(2, eq, 'Silver')

    This will look at the third field in the record and see if it equals
    'Silver'.
    """

    def __init__(self, field, op, value):
        self.field = field
        self.op = op
        self.value = value

    def get_value_func(self, item):
        """
        Returns a function that when supplied a record will return a
        value.  It is used by filter_func() to return dynamically
        the requested field value or a string constant.

        :param item: If an int is supplied, this is assumed to be a
                     field number, in which case is used to split the
                     record using the Delegate owner's delim and return
                     the item.  If a str, it is assumed to be a constant
                     and so will just be returned.
        :return:     A function to be used to supply a value to a term
                     in the function returned by filter_func().
        """
        global _zero_based

        if isinstance(item, int):
            if not _zero_based:
                item -= 1

            def func(rec):
                result = rec[item]

                if result is None:
                    raise RuntimeError('Attempt to return None from rec {}'.format(rec))

                return result
        else:
            def func(rec):
                raise RuntimeError("Can't handle item '{}'".format(item))

        return func

    def __call__(self):
        """Returns a function that takes the entire record and evaluates the configured condition."""
        func1 = self.get_value_func(self.field)

        def func(rec):
            return self.op(func1(rec), self.value)

        return func

    def __repr__(self):
        return 'Cond({}, {}, {})'.format(self.field, self.op.__name__, self.value)


def eq(a, b):
    """Evaluate whether a equals b."""
    return a == b


def ne(a, b):
    """Evaluate whether a does not equal b."""
    return a != b


def gt(a, b):
    """Evaluate whether a is greater than b."""
    return a > b


def gte(a, b):
    """Evaluate whether a is greater than or equal to b."""
    return a >= b


def lt(a, b):
    """Evaluate whether a is less than b."""
    return a < b


def lte(a, b):
    """Evaluate whether a is less than or equal to b."""
    return a <= b


# would have preferred to name this 'in', but that is a reserved word
def is_in(a, b):
    """Evaluate whether a is in b."""
    return a in b


class Key(object):
    """Callable class that returns a key calculation function when invoked."""

    def __init__(self, *args):
        self.args = args

    def __call__(self):
        """Returns a function that when passed a record returns the key values."""
        global _zero_based
        args = self.args

        if not _zero_based:
            args = [(a[0] - 1, a[1]) if isinstance(a, tuple) else a - 1 for a in args]

        def func(rec):
            # if the argument was a tuple, then the second item is a type
            # to which the value in the first item should be cast

            result = [
                a[1](rec[a[0]]) if isinstance(a, tuple) else rec[a]
                for a in args
            ]

            return result

        return func


class FullRecord(Key):
    """Subclass of Key that returns the entire record as the key."""

    def __call__(self):
        """Returns a function that in turn returns the entire record as the key."""
        def func(rec):
            return rec

        return func


class Reformat(object):
    """Base class for providing custom transformations."""

    def transform(self, in_rec):
        """Returns the transformed record.  Override as needed."""
        return in_rec


class AbstractChainable(object):
    """Abstract class that provides all base chaining functionality.
       Subclasses must implement __iter__()."""

    def __init__(self):
        self.parent = None
        self.iterable = None

    def chain(self, new_child):
        """Connects new instance to the last instance in the chain then returns the new instance."""
        new_child.parent = self
        return new_child

    def sort(self, *sort_params, **kwargs):
        """Adds a sort step to the chain."""
        key_inst = Key(*sort_params) if sort_params else None
        return self.chain(SortChainable(key_inst, **kwargs))

    def filter(self, field, op, value):
        """Adds a filter step to the chain."""
        filter_inst = Cond(field, op, value)
        return self.chain(FilterChainable(filter_inst))

    def grep(self, regex):
        """Adds a grep (filter using regexp) step to the chain."""
        filter_func = re.compile(regex).search
        return self.chain(FilterChainable(filter_func))

    def transform(self, transform_item):
        """Adds a transformation step to the chain."""
        return self.chain(TransformChainable(transform_item))

    def cut(self, *cut_params):
        """Adds a cut step to the chain."""

        # a Key is really just a class that creates a function to extract
        # fields from a record in a certain way, so it can also be
        # re-purposed to act like the Unix "cut" utility
        key_inst = Key(*cut_params)
        return self.chain(TransformChainable(key_inst()))

    def reduce(self, transform_class, *sort_params):
        """Adds a reduce step (i.e., aggregation or rollup) to the chain."""
        key_inst = Key(*sort_params)
        return self.chain(ReduceChainable(key_inst, transform_class))

    def show(self, row_number=False, print_function=None):
        """Displays all records in the stream to stdout or using the print_function, if supplied."""
        global _verbose, writeln

        if not _verbose:
            return self

        if print_function is None:
            print_function = writeln

        if not row_number:
            for rec in self:
                print_function(rec)
        else:
            for i, rec in enumerate(self):
                print_function('{}: {}'.format(i + 1, rec))

        return self

    def head(self, print_function=None):
        """Displays the first 5 records in the stream to stdout or using the print_function, if supplied."""
        global _verbose, writeln

        if not _verbose:
            return self

        if print_function is None:
            print_function = writeln

        for i, rec in enumerate(self):
            print_function(rec)

            if i == 4:
                break

        return self

    def count(self, message=None, print_function=None):
        """Displays the total count of records in the stream to stdout or using the print_function, if supplied."""
        global _verbose, writeln

        if not _verbose:
            return self

        if print_function is None:
            print_function = writeln

        print_function('%s %s' % (message or 'count', len(self)))

        return self

    def __iter__(self):
        """Subclasses must implement to yield records in the stream."""
        raise NotImplementedError('concrete subclasses must implement __iter__()')

    def __len__(self):
        """Permits AbstractChainable to function correctly if len() is invoked on it."""

        # invoking iter avoids recursive behavior of len(list(self))
        return len(list(iter(self)))


class IterReader(AbstractChainable):
    """Concrete subclass of AbstractChainable that reads from an iterable source."""

    def __init__(self, iterable):
        super(IterReader, self).__init__()
        self.iterable = iterable

    def __iter__(self):
        """Yields records from an iterable source."""
        if self.iterable is None:
            self.iterable = []

        for i in self.iterable:
            yield i


class FileReader(AbstractChainable):
    """Concrete subclass of AbstractChainable that iterates over the records of a file."""

    def __init__(self, filename):
        super(FileReader, self).__init__()
        self.filename = filename

    def __iter__(self):
        """Yield records from a file."""
        fp = open(self.filename)

        for rec in fp:
            yield self.prep_record(rec)

        fp.close()

    def prep_record(self, rec):
        """Returns a data record with record delimiters stripped off."""
        return rec.strip()


class CsvReader(FileReader):
    """Concrete subclass of AbstractChainable that iterates over the records
    of a file and splits them into fields using a delimiter."""

    def __init__(self, filename, delim=None, headers=None):
        super(CsvReader, self).__init__(filename)
        self.delim = delim or ','
        self.headers = headers if headers is not None else 1
        self.header_records = []

    def __iter__(self):
        """Yields records split into fields using the delimiter."""
        fp = open(self.filename)

        if self.header_records:
            for i in range(0, self.headers):
                fp.readline()
        else:
            for i in range(0, self.headers):
                self.header_records.append(fp.readline().strip())

        for rec in fp:
            yield self.prep_record(rec)

        fp.close()

    def prep_record(self, rec):
        """Returns a record stripped of record delimiters and split by the field delimiter."""
        return rec.strip().split(self.delim)


class SortChainable(AbstractChainable):
    """A chainable subclass of AbstractChainable that sorts records."""

    def __init__(self, key, reverse=None):
        super(SortChainable, self).__init__()
        self.key = key
        self.reverse = reverse or False

    def __iter__(self):
        """Yield records sorted by the specified key."""
        if isinstance(self.key, Key):
            key = self.key()
        else:
            key = None

        for rec in sorted(self.parent, key=key, reverse=self.reverse):
            yield rec


class FilterChainable(AbstractChainable):
    """A chainable subclass of AbstractChainable that filters records."""

    def __init__(self, filter_inst):
        super(FilterChainable, self).__init__()
        self.filter_inst = filter_inst

    def __iter__(self):
        """Yields records filtered by the given Cond or function."""
        if isinstance(self.filter_inst, Cond):
            filter_func = self.filter_inst()
        elif callable(self.filter_inst):
            filter_func = self.filter_inst
        else:
            raise RuntimeError('only works with a Cond instance or re.compile.search')

        for rec in filter(filter_func, self.parent):
            yield rec


class TransformChainable(AbstractChainable):
    """A chainable subclass of AbstractChainable that transforms records."""

    def __init__(self, transform_item):
        super(TransformChainable, self).__init__()
        self.transform_item = transform_item

    def __iter__(self):
        """Yields transformed records."""
        if self.transform_item.__class__.__name__ == 'function':
            xform = self.transform_item
        elif issubclass(self.transform_item, Reformat):
            xform = self.transform_item().transform
        else:
            raise RuntimeError('compatible only with a function or Reformat')

        for rec in self.parent:
            yield xform(rec)


class AbstractReducer(object):
    """An abstract class that provides all methods needed by ReduceChainable.
    This class is meant to act as a template for implementing rollups,
    aggregates and other kinds of key-based summarizations."""

    def initialize(self, key):
        """Invoked at the beginning of a reduce operation."""
        pass

    def key_change(self, prev_key, curr_key):
        """Invoked every time the key changes."""
        pass

    def reduce(self, key, in_rec):
        """Invoked for every record flowing through the reduce operation."""
        pass

    def output(self, key, prev_rec):
        """Invoked every time the key changes as well as at the very end."""
        return key


class Uniq(AbstractReducer):
    """Subclass of AbstractReducer that returns unique records."""
    pass


class UniqCount(Uniq):
    """Subclass of Uniq that counts the number of records for a given key."""

    def __init__(self):
        self.context = 0

    def initialize(self, key):
        self.context = 0

    def key_change(self, prev_key, curr_key):
        self.context = 0

    def reduce(self, key, in_rec):
        self.context += 1

    def output(self, key, prev_rec):
        return [key, 'count', self.context]


class ReduceChainable(AbstractChainable):
    """A chainable subclass of AbstractChainable that summarizes records
    based on a key."""

    def __init__(self, key_inst, transform_class):
        super(ReduceChainable, self).__init__()
        self.key_inst = key_inst
        self.transform_class = transform_class

    def __iter__(self):
        """Yield records from the output() method of the given AbstractReducer
        as governed by the supplied key."""

        xform = self.transform_class()
        key_func = self.key_inst()
        prev_key = None
        prev_rec = None
        curr_key = None
        curr_rec = None

        for curr_rec in self.parent:
            curr_key = key_func(curr_rec)

            if prev_key is None:
                prev_key = curr_key
                xform.initialize(curr_key)

            if curr_key == prev_key:
                xform.reduce(curr_key, curr_rec)

            elif curr_key > prev_key:
                yield xform.output(prev_key, prev_rec)

                xform.key_change(prev_key, curr_key)
                xform.reduce(curr_key, curr_rec)

                prev_key = curr_key

            prev_rec = curr_rec

        yield xform.output(curr_key, curr_rec)
