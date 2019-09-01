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


# verbose is used to cleanly enable or silence all .count(), .show()
# and .head() operations

_verbose = True


def set_verbose(verbose):
    global _verbose

    if verbose:
        _verbose = True
    else:
        _verbose = False


def get_verbose():
    global _verbose
    return _verbose


def flatten(list_of_lists):
    return [item for inner_list in list_of_lists for item in inner_list]


class Cond(object):
    """Callable class that generates a function that can be used with filter()

    The canonical use is:

        Cond(2, eq, 'Silver')

    This will look at the third field in the record and see if it equals
    'Silver'.  Generally, this class is intended to be subclassed.
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

        if isinstance(item, int):
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
        func1 = self.get_value_func(self.field)

        def func(rec):
            return self.op(func1(rec), self.value)

        return func

    def __repr__(self):
        return f'Cond({self.field}, {self.op.__name__}, {self.value})'


def eq(a, b): return a == b


def ne(a, b): return a != b


def gt(a, b): return a > b


def gte(a, b): return a >= b


def lt(a, b): return a < b


def lte(a, b): return a <= b

# would have preferred to name this 'in', but that is a reserved word
def is_in(a, b): return a in b


class Key(object):
    """Callable class that returns a key calculation function when invoked"""

    def __init__(self, *args):
        self.args = args

    def __call__(self):
        args = self.args

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

    def __call__(self):
        def func(rec):
            return rec

        return func


class Reformat(object):

    def transform(self, in_rec):
        return in_rec


class AbstractChainable(object):

    def __init__(self):
        self.parent = None
        self.iterable = None

    def chain(self, new_child):
        new_child.parent = self
        return new_child

    def sort(self, *sort_params, reverse=False):
        key_inst = Key(*sort_params) if sort_params else None
        return self.chain(SortChainable(key_inst, reverse=reverse))

    def filter(self, field, op, value):
        filter_inst = Cond(field, op, value)
        return self.chain(FilterChainable(filter_inst))

    def grep(self, regex):
        filter_func = re.compile(regex).search
        return self.chain(FilterChainable(filter_func))

    def transform(self, transform_item):
        return self.chain(TransformChainable(transform_item))

    def cut(self, *cut_params):
        # a Key is really just a class that creates a function to extract
        # fields from a record in a certain way, so it can also be
        # repurposed to act like the Unix "cut" utility
        key_inst = Key(*cut_params)
        return self.chain(TransformChainable(key_inst()))

    def reduce(self, transform_class, *sort_params):
        key_inst = Key(*sort_params)
        return self.chain(ReduceChainable(key_inst, transform_class))

    def show(self, row_number=False, print_function=None):
        global _verbose
        if not _verbose:
            return self

        if print_function is None:
            print_function = print

        if not row_number:
            for rec in self:
                print_function(rec)
        else:
            for i, rec in enumerate(self):
                print_function('{}: {}'.format(i + 1, rec))

        return self

    def head(self, print_function=None):
        global _verbose
        if not _verbose:
            return self

        if print_function is None:
            print_function = print

        for i, rec in enumerate(self):
            print_function(rec)

            if i == 4:
                break

        return self

    def count(self, message=None, print_function=None):
        global _verbose
        if not _verbose:
            return self

        if print_function is None:
            print_function = print

        print_function('%s %s' % (message or 'count', len(self)))

        return self

    def __iter__(self):
        raise NotImplementedError('concrete subclasses must implement __iter__()')

    def __len__(self):
        # invoking iter avoids recursive behavior of len(list(self))
        return len(list(iter(self)))


class IterReader(AbstractChainable):

    def __init__(self, iterable):
        super().__init__()
        self.iterable = iterable

    def __iter__(self):
        if self.iterable is None:
            self.iterable = []

        for i in self.iterable:
            yield i


class FileReader(AbstractChainable):

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def __iter__(self):
        fp = open(self.filename)

        for rec in fp:
            yield self.prep_record(rec)

        fp.close()

    def prep_record(self, rec):
        return rec.strip()


class CsvReader(FileReader):

    def __init__(self, filename, delim=None, headers=None):
        super().__init__(filename)
        self.delim = delim or ','
        self.headers = headers if headers is not None else 1
        self.header_records = []

    def __iter__(self):
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
        return rec.strip().split(self.delim)


class SortChainable(AbstractChainable):

    def __init__(self, *sort_params, reverse=False):
        super().__init__()
        self.sort_params = sort_params
        self.reverse = reverse

    def __iter__(self):
        if isinstance(self.sort_params[0], Key):
            key = self.sort_params[0]()
        else:
            key = None

        for rec in sorted(self.parent, key=key, reverse=self.reverse):
            yield rec


class FilterChainable(AbstractChainable):

    def __init__(self, filter_inst):
        super().__init__()
        self.filter_inst = filter_inst

    def __iter__(self):
        if isinstance(self.filter_inst, Cond):
            filter_func = self.filter_inst()
        elif callable(self.filter_inst):
            filter_func = self.filter_inst
        else:
            raise RuntimeError('only works with a Cond instance or re.compile.search')

        for rec in filter(filter_func, self.parent):
            yield rec


class TransformChainable(AbstractChainable):

    def __init__(self, transform_item):
        super().__init__()
        self.transform_item = transform_item

    def __iter__(self):
        if self.transform_item.__class__.__name__ == 'function':
            xform = self.transform_item
        elif issubclass(self.transform_item, Reformat):
            xform = self.transform_item().transform
        else:
            raise RuntimeError('compatible only with a function or Reformat')

        for rec in self.parent:
            yield xform(rec)


class AbstractReducer(object):

    def initialize(self, key):
        pass

    def key_change(self, prev_key, curr_key):
        pass

    def reduce(self, key, in_rec):
        pass

    def output(self, key, prev_rec):
        return key


class Uniq(AbstractReducer):
    pass


class UniqCount(Uniq):

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

    def __init__(self, key_inst, transform_class):
        super().__init__()
        self.key_inst = key_inst
        self.transform_class = transform_class

    def __iter__(self):
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
