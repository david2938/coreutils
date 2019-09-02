import unittest
from datetime import datetime
import tempfile
from coreutils import *


class Collector(object):

    def __init__(self):
        self.collector = []

    def __call__(self, *objects, sep='', end='\n', file=None, flush=False):
        # intended to make this object a callable replacement to print()
        self.collector.append((*objects, {'sep': sep, 'end': end, 'file': file, 'flush': flush}))


class TestCollector(unittest.TestCase):

    def test_basic_usage(self):
        print_replacement = Collector()

        print_replacement('Hello World')

        self.assertEqual(len(print_replacement.collector), 1)


class TestVerboseFunction(unittest.TestCase):

    def test_set_and_get(self):
        set_verbose(True)

        self.assertTrue(get_verbose())

        set_verbose(False)

        self.assertFalse(get_verbose())

        set_verbose('true')

        self.assertTrue(get_verbose())

        # oddly, this will be true because a non-zero length string evaluate to True, regardless of value

        set_verbose('false')

        self.assertTrue(get_verbose())

        # setting verbose to an empty list will make it false since an empty list evaluates to False
        set_verbose([])

        self.assertFalse(get_verbose())


class TestFlatten(unittest.TestCase):

    def test_intended_cases(self):
        i = [[1], [2], [3]]

        self.assertEqual([1, 2, 3], flatten(i))

        i = [['a', 'b'], ['c', 'd', 'e']]

        self.assertEqual(['a', 'b', 'c', 'd', 'e'], flatten(i))

        i = [['a'], [1, 'b'], [2, 'c', 2, 2], ['d', '3', 3, 2 + 1]]

        self.assertEqual(['a', 1, 'b', 2, 'c', 2, 2, 'd', '3', 3, 3], flatten(i))


input_list = [
    ['59693-IL-9641352', 'Georgia', 'Green', 95.05, 7],
    ['69097-MH-9660859', 'France', 'Green', 134.15, 60],
    ['82397-OL-5279119', 'Italy', 'Blue', 115.13, 5],
    ['55172-FK-4803787', 'Spain', 'Blue', 120.95, 2],
    ['94894-SM-6632145', 'Austria', 'Blue', 114.51, 2],
    ['29977-AD-6660666', 'Turkey', 'Green', 98.71, 11],
    ['01335-EJ-3213682', 'France', 'Red', 133.94, 18],
    ['44276-SX-1910741', 'Germany', 'Purple', 105.99, 1],
    ['27188-AO-8505663', 'Spain', 'Blue', 107.64, 23],
    ['29587-JN-9389756', 'Ireland', 'Blue', 113.58, 9],
    ['99860-ZW-4745487', 'Poland', 'Blue', 92.48, 3],
    ['34994-JR-5047501', 'France', 'Blue', 135.91, 17],
    ['91659-RZ-5186202', 'Sweden', 'Green', 112.48, 4],
    ['12032-LZ-7926982', 'Germany', 'Purple', 93.71, 14],
    ['71662-GO-4658117', 'Norway', 'Red', 103.54, 1],
    ['89874-KA-6452420', 'Turkey', 'Blue', 79.54, 15],
    ['26097-FF-5759042', 'Italy', 'Blue', 111.72, 8],
    ['08244-KJ-6725583', 'Georgia', 'Green', 90.96, 13],
    ['23138-BX-9971854', 'Poland', 'Green', 84.18, 5],
    ['70888-OK-5965389', 'Germany', 'Green', 111.0, 11],
    ['03935-SA-5929589', 'Malta', 'Green', 102.49, 6],
    ['02992-SP-9382892', 'Montenegro', 'Green', 83.69, 1],
    ['12983-FW-8144797', 'Spain', 'Green', 84.87, 25],
    ['19017-HN-3601064', 'Spain', 'Blue', 120.24, 19],
]


class TestCond(unittest.TestCase):

    def test_basic_operation(self):
        global input_list

        condition = Cond(1, eq, 'Spain')

        self.assertTrue(len(list(filter(condition(), input_list))), 4)

        # or you can do this

        filter_cond = condition()

        self.assertTrue(len(list(filter(filter_cond, input_list))), 4)


class TestOperatorFunctions(unittest.TestCase):

    def test_em_all(self):
        self.assertTrue(eq(1, 1))
        self.assertTrue(eq('a', 'a'))
        self.assertTrue(eq(47.5, 47.5))

        dt1 = datetime(1967, 5, 23, 12, 37, 56)
        dt2 = datetime(1967, 5, 23, 12, 37, 56)
        dt3 = datetime(1967, 5, 23, 12, 37, 57)

        self.assertTrue(eq(dt1, dt2))
        self.assertFalse(eq(dt1, dt3))
        self.assertTrue(ne(dt1, dt3))
        self.assertFalse(not ne(dt1, dt3))

        self.assertFalse(eq(1, 2))

        self.assertTrue(gt(2, 1))
        self.assertTrue(gte(1, 1))
        self.assertTrue(gte(2, 1))
        self.assertFalse(gte(1, 2))
        self.assertTrue(lt('a', 'b'))
        self.assertTrue(lt('a', 'aa'))
        self.assertFalse(lt('aa', 'a'))
        self.assertFalse(lt('a', 'a'))
        self.assertFalse(lt('b', 'a'))
        self.assertTrue(lt('a', 'b'))
        self.assertTrue(lte('a', 'b'))
        self.assertTrue(lte('a', 'a'))
        self.assertFalse(lte('b', 'a'))


class TestCond(unittest.TestCase):

    def test_basic_operation(self):
        c = Cond(0, eq, 1)

        self.assertTrue(callable(c))

        func = c()
        i = [1]

        self.assertTrue(func(i))

        i = [1, 2]

        self.assertTrue(func(i))

        i = ['1', 2]

        self.assertFalse(func(i))

        c = Cond(0, eq, '1')
        func = c()

        self.assertTrue(func(i))

    def test_use_in_filter(self):
        global input_list

        c = Cond(1, eq, 'Turkey')

        self.assertEqual(len(list(filter(c(), input_list))), 2)

        # although not expressly intended, you can swap out the operator on the instance

        c.op = ne

        self.assertEqual(len(list(filter(c(), input_list))), 22)

        # the function obtained by calling the instance is still tied to that instance,
        # so even if you obtain the function and then change the operator, the function
        # will adopt the change to the instance (it's like they are entangled!)

        func = c()
        c.op = eq

        # the length should still be 22 because the function is using the 'ne' function

        self.assertEqual(len(list(filter(func, input_list))), 2)

    def test_is_in_str_set_list_tuple(self):
        data = [
            [52, 'David'],
            [12, 'Charlie'],
            [43, 'Jeff'],
            [61, 'James']
        ]
        long_str = 'David Charlie Jeff'
        c = Cond(1, is_in, long_str)
        f = c()

        self.assertEqual(len(list([_ for _ in data if f(_)])), 3)

        s = {'David', 'Charlie', 'Jeff'}
        c = Cond(1, is_in, s)
        f = c()

        self.assertEqual(len(list([_ for _ in data if f(_)])), 3)

        l1 = list(s)

        c = Cond(1, is_in, l1)
        f = c()

        self.assertEqual(len(list([_ for _ in data if f(_)])), 3)

        t = tuple(_ for _ in s)
        c = Cond(1, is_in, t)
        f = c()

        self.assertEqual(len(list([_ for _ in data if f(_)])), 3)

    def test_use_in_for_loop(self):
        data = [
            [52, 'David'],
            [12, 'Charlie'],
            [43, 'Jeff'],
            [61, 'James']
        ]
        c = Cond(0, lt, 61)
        f = c()
        matched = 0

        for d in data:
            if f(d):
                matched += 1

        self.assertEqual(3, matched)

        c = Cond(1, is_in, ['David', 'Jeff'])
        f = c()
        matched = 0

        for d in data:
            if f(d):
                matched += 1

    def test_exception(self):
        data = [None]
        c = Cond(0, eq,  1)
        f = c()

        self.assertRaisesRegex(RuntimeError, "Attempt to return None from rec", f, data)

        c = Cond('David', eq, 1)
        f = c()

        self.assertRaisesRegex(RuntimeError, "Can't handle item", f, data)

    def test_repr(self):
        c = Cond(0, eq,  1)

        self.assertEqual(c.__repr__(), 'Cond(0, eq, 1)')

class TestKey(unittest.TestCase):

    def test_basic_operation(self):
        rec = ['David', '52', 127.98]
        k = Key(0)

        self.assertTrue(callable(k))

        f = k()

        self.assertTrue(f(rec), 'David')
        self.assertTrue(Key((1, int))()(rec), 52)
        self.assertTrue(Key(2)()(rec), 127.98)
        self.assertEqual(Key(0, (1, int))()(rec), ['David', 52])
        self.assertEqual(Key((1, float), 2)()(rec), [52.0, 127.98])

    def test_comparing_key_func_results(self):
        a = ['09846WB8636633', 'Italy', 'Blue', 361.69, 5]
        b = ['78590JQ3204809', 'Spain', 'Blue', 379.97, 2]
        k = Key(0)

        self.assertTrue(k()(a) < k()(b))

        # use an operator function, just for fun

        self.assertTrue(lt(k()(a), k()(b)))
        self.assertTrue(lte(k()(a), k()(b)))

        kf = Key(2, 1)()

        self.assertTrue(kf(a) < kf(b))

        kf = Key(4, 3)()

        self.assertTrue(kf(a) > kf(b))

    def test_key_in_simple_sort(self):
        global input_list
        k = Key(0)
        sorted_list = sorted(input_list, key=k())

        self.assertEqual(sorted_list[0][0], '01335-EJ-3213682')
        self.assertEqual(sorted_list[-1][0], '99860-ZW-4745487')

        k = Key(3)
        sorted_list = sorted(input_list, key=k())

        self.assertEqual(sorted_list[0][3], 79.54)
        self.assertEqual(sorted_list[-1][3], 135.91)

        # key is non-deterministic, but at least its value should be sorted
        k = Key(4)
        sorted_list = sorted(input_list, key=k())

        self.assertEqual(sorted_list[0][4], 1)
        self.assertEqual(sorted_list[-1][4], 60)

    def test_key_in_sort_with_cast(self):
        data = [
            ['94970PT4045197', 'Spain', 'Blue', '377.73', 19],
            ['25775GT9423594', 'Montenegro', 'Green', '262.93', 1],
            ['65128VB5535475', 'Spain', 'Green', '266.62', 25],
        ]
        k = Key((3, float))
        sorted_data = sorted(data, key=k())

        self.assertTrue(sorted_data[0][3] == '262.93')
        self.assertTrue(sorted_data[-1][3] == '377.73')

    def test_complex_key_sort(self):
        global input_list
        k = Key(2, 4, 3)
        sorted_list = sorted(input_list, key=k())

        self.assertEqual(sorted_list[0], ['94894-SM-6632145', 'Austria', 'Blue', 114.51, 2])
        self.assertEqual(sorted_list[-1], ['01335-EJ-3213682', 'France', 'Red', 133.94, 18])


class TestFullRecordKey(unittest.TestCase):

    def test_using_sorted(self):
        global input_list
        k = FullRecord()
        sorted_list = sorted(input_list, key=k())

        self.assertEqual(sorted_list[0], ['01335-EJ-3213682', 'France', 'Red', 133.94, 18])
        self.assertEqual(sorted_list[-1], ['99860-ZW-4745487', 'Poland', 'Blue', 92.48, 3])


class TestReformat(unittest.TestCase):

    def test_basic_operation(self):
        rec = ['94970PT4045197', 'Spain', 'Blue', '377.73', 19]
        ref = Reformat()

        self.assertEqual(rec, ref.transform(rec))

    def test_subclassing_reformat(self):
        class SimpleReformat(Reformat):
            def transform(self, in_rec):
                return float(in_rec[3])

        rec = ['94970PT4045197', 'Spain', 'Blue', '377.73', 19]
        ref = SimpleReformat()

        self.assertEqual(ref.transform(rec), 377.73)


class TestAbstractChainable(unittest.TestCase):

    def test_chain(self):
        a = AbstractChainable()
        a2 = a.chain(AbstractChainable())

        self.assertNotEqual(id(a), id(a2))
        self.assertEqual(a, a2.parent)
        self.assertIsInstance(a2, AbstractChainable)

    def test_sort(self):
        a = AbstractChainable()
        sp = (1, (2, int), 3)
        k = Key(*sp)
        s = a.sort(*sp)

        self.assertNotEqual(id(a), id(s))
        self.assertEqual(a, s.parent)
        self.assertIsInstance(s, SortChainable)
        self.assertEqual(sp, s.sort_params[0].args)

        record = ('not_used', 'f1', '2', 3)
        key_func1 = k()
        key_func2 = s.sort_params[0]()
        key_val1 = key_func1(record)
        key_val2 = key_func2(record)

        self.assertEqual(key_val1, key_val2)

    def test_filter(self):
        a = AbstractChainable()
        fargs = (0, eq, 42)
        f = a.filter(*fargs)
        c = Cond(*fargs)

        self.assertNotEqual(id(a), id(f))
        self.assertEqual(a, f.parent)
        self.assertIsInstance(f, FilterChainable)
        self.assertEqual(fargs[0], f.filter_inst.field)
        self.assertEqual(fargs[1], f.filter_inst.op)
        self.assertEqual(fargs[2], f.filter_inst.value)

        data = [[41], [42], [43]]
        ffunc = f.filter_inst()
        cfunc = c()
        ffunc_filtered = list(filter(ffunc, data))
        cfunc_filtered = list(filter(cfunc, data))

        self.assertEqual(ffunc_filtered, cfunc_filtered)

    def test_grep(self):
        a = AbstractChainable()
        g = a.grep(r'foo')

        self.assertEqual(a, g.parent)
        self.assertNotEqual(id(a), id(g))
        self.assertEqual(g.filter_inst.__name__, 'search')

        data = ['foobaz', 'bazbar', 'fizzbin', 'fizfoobar', 'bazfoo']
        filtered = list(filter(g.filter_inst, data))

        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered, ['foobaz', 'fizfoobar', 'bazfoo'])

        g2 = a.grep(r'^foo')
        filtered = list(filter(g2.filter_inst, data))

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered, ['foobaz'])

        g3 = a.grep(r'foo$')
        filtered = list(filter(g3.filter_inst, data))

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered, ['bazfoo'])

        g4 = a.grep(r'^foo$')
        filtered = list(filter(g4.filter_inst, data))

        self.assertEqual(len(filtered), 0)
        self.assertEqual(filtered, [])


    def test_transform(self):
        a = AbstractChainable()
        t = a.transform(Reformat)

        self.assertNotEqual(id(a), id(t))
        self.assertEqual(a, t.parent)
        self.assertEqual(Reformat, t.transform_item)

        ref_inst = Reformat()
        t_inst = t.transform_item()

        self.assertNotEqual(ref_inst, t_inst)

        record = ('David', 42, 1967.523)
        ref_result = ref_inst.transform(record)
        t_result = t_inst.transform(record)

        self.assertEqual(ref_result, t_result)

    def test_cut(self):
        a = AbstractChainable()
        cparams = (1, (2, str))
        c = a.cut(*cparams)

        self.assertNotEqual(a, c)
        self.assertNotEqual(id(a), id(c))
        self.assertEqual(a, c.parent)

        record = ('David', 42, 1967.523)
        k = Key(*cparams)
        kfunc = k()
        kfunc_result = kfunc(record)
        cxform_result = c.transform_item(record)

        self.assertEqual(kfunc_result, cxform_result)

    def test_reduce(self):
        a = AbstractChainable()
        k = (0, 1, 2)
        r = a.reduce(Uniq, *k)

        # just test the operation of the reduce() method and that it correctly
        # configures the classes correctly

        self.assertNotEqual(a, r)
        self.assertNotEqual(id(a), id(r))
        self.assertEqual(r.parent, a)
        self.assertEqual(r.key_inst.args, k)
        self.assertEqual(r.transform_class, Uniq)

    def test_exception(self):
        a = AbstractChainable()

        self.assertRaisesRegex(NotImplementedError, "concrete subclasses must implement __iter__()", list, a)


class TestIterReader(unittest.TestCase):

    def test_none(self):
        i = IterReader(None)

        self.assertEqual(0, len(i))

    def test_empty_list(self):
        i = IterReader([])

        self.assertEqual(0, len(i))

    def test_list_of_ints(self):
        li = [1, 2, 3]
        i = IterReader(li)

        self.assertEqual(3, len(i))

        i2 = list(i)

        self.assertEqual(i2, li)

    def test_list_of_csv_strings(self):
        records = [
            'David,52,5/23/1967',
            'Charlie,10,6/11/2011',
            'Michelle,55,1/31/1967',
            'Mutti,83,8/01/1936'
        ]
        i = IterReader(records)

        self.assertEqual(list(i), records)

    def test_list_of_heterogeneous_values(self):
        records = [
            'David,52,5/23/1967',
            'Charlie,10,6/11/2011',
            'Michelle,55,1/31/1967',
            'Mutti,83,8/01/1936'
        ]
        split_records = map(lambda f: [f.split(',')[0], int(f.split(',')[1]), f.split(',')[2]], records)
        i = IterReader(split_records)

        self.assertEqual(list(i), list(split_records))

    def test_show(self):
        global input_list

        c = Collector()
        i = IterReader(input_list).show(print_function=c)

        self.assertEqual(len(c.collector), len(input_list))

        c2 = Collector()
        r = i.show(print_function=c2, row_number=True)

        for n, rec in enumerate(c2.collector):
            rec_no = int(rec[0].split(':')[0])
            self.assertEqual(n + 1, rec_no)

        self.assertEqual(r, i)

        set_verbose(False)

        c2 = Collector()
        r = i.show(print_function=c2)

        self.assertEqual(len(c2.collector), 0)
        self.assertEqual(i, r)

        set_verbose(True)

        c3 = Collector()
        r = i.show(print_function=c3)

        self.assertEqual(len(c.collector), len(input_list))
        self.assertEqual(i, r)

    def test_head(self):
        global input_list

        c = Collector()
        i = IterReader(input_list)
        h = i.head(print_function=c)

        self.assertEqual(len(c.collector), 5)
        self.assertEqual(i, h)

        set_verbose(False)

        c2 = Collector()
        h = i.head(print_function=c2)

        self.assertEqual(len(c2.collector), 0)
        self.assertEqual(h, i)

        set_verbose(True)

        c3 = Collector()
        h = i.head(print_function=c3)

        self.assertEqual(len(c3.collector), 5)
        self.assertEqual(h, i)


    def test_count(self):
        global input_list

        c = Collector()
        i = IterReader(input_list)
        n = i.count(print_function=c)

        self.assertEqual(c.collector[0][0], 'count %s' % len(input_list))
        self.assertEqual(n, i)

        set_verbose(False)

        c2 = Collector()
        n = i.count(print_function=c2)

        self.assertEqual(len(c2.collector), 0)
        self.assertEqual(n, i)

        set_verbose(True)

        c3 = Collector()
        n = i.count(print_function=c3)

        self.assertEqual(c3.collector[0][0], 'count %s' % len(input_list))
        self.assertEqual(n, i)



class TestFileReader(unittest.TestCase):

    def test_basic_operation(self):
        global input_list

        with tempfile.NamedTemporaryFile(mode='w') as fp:
            lines = [','.join(map(str, rec)) for rec in input_list]
            fp.writelines([_ + '\n' for _ in lines])
            fp.flush()

            fr = FileReader(fp.name)
            recs = list(fr)

            self.assertEqual(lines, recs)


class TestCsvReader(unittest.TestCase):

    def test_basic_operation(self):
        global input_list

        with tempfile.NamedTemporaryFile(mode='w') as fp:
            lines = [','.join(map(str, rec)) for rec in input_list]
            fp.writelines([_ + '\n' for _ in lines])
            fp.flush()

            fr = CsvReader(fp.name)
            recs = list(fr)

            # CsvReader can only return individual fields as strings, so
            # convert the input_list to one of all str

            input_list_str = [list(map(str, rec)) for rec in input_list]

            self.assertEqual(input_list_str[1:], recs)


class TestSortChainable(unittest.TestCase):

    def test_sort_with_key(self):
        global input_list

        s = IterReader(input_list).sort(2, 3)

        self.assertEqual(len(input_list), len(s))

        first = ['89874-KA-6452420', 'Turkey', 'Blue', 79.54, 15]
        last = ['01335-EJ-3213682', 'France', 'Red', 133.94, 18]

        s_list = list(s)

        self.assertEqual(s_list[0], first)
        self.assertEqual(s_list[-1], last)

    def test_sort_no_key(self):
        global input_list

        s = IterReader(input_list).sort()

        # should do a full-record sort, which means these are the first/last

        first = ['01335-EJ-3213682', 'France', 'Red', 133.94, 18]
        last = ['99860-ZW-4745487', 'Poland', 'Blue', 92.48, 3]

        s_list = list(s)

        self.assertEqual(s_list[0], first)
        self.assertEqual(s_list[-1], last)


class TestFilterChainable(unittest.TestCase):

    def test_filter(self):
        global input_list

        s = IterReader(input_list).filter(2, eq, 'Red')

        expected =[
            ['01335-EJ-3213682', 'France', 'Red', 133.94, 18],
            ['71662-GO-4658117', 'Norway', 'Red', 103.54, 1]
        ]
        s_list = list(s)

        self.assertEqual(s_list, expected)

    def test_grep(self):
        data = [
            '08/31/2019 Lorem ipsum dolor sit amet',
            '09/01/2019 consectetur adipiscing elit',
            '09/02/2019 sed do eiusmod tempor incididunt',
            '09/03/2019 ut labore et dolore magna aliqua'
        ]

        i = IterReader(data).grep('ore')
        expected = [
            '08/31/2019 Lorem ipsum dolor sit amet',
            '09/03/2019 ut labore et dolore magna aliqua',
        ]

        self.assertEqual(len(i), 2)
        self.assertEqual(list(i), expected)

        self.assertEqual(list(IterReader(data).grep(r'9.*2.*sed')), ['09/02/2019 sed do eiusmod tempor incididunt'])


    def test_exception(self):
        global input_list

        i = IterReader(input_list)
        manual_filter = i.chain(FilterChainable(object()))

        self.assertRaisesRegex(RuntimeError, 'only works with a Cond instance or', list, manual_filter)

    def test_multiple_filters(self):
        global input_list

        s = IterReader(input_list).filter(4, eq, 11).filter(1, eq, 'Turkey')

        expected = ['29977-AD-6660666', 'Turkey', 'Green', 98.71, 11]
        s_list = list(s)

        self.assertEqual(len(s), 1)
        self.assertEqual(len(s_list), 1)
        self.assertEqual(s_list[0], expected)


class TeestTransformChainable(unittest.TestCase):

    def test_noop_transform(self):
        global input_list

        i = IterReader(input_list).transform(Reformat)

        self.assertEqual(list(i), input_list)

    def test_real_transform(self):
        global input_list

        class TestReformat(Reformat):

            def transform(self, in_rec):
                return f'{in_rec[1]}-{in_rec[4]:02d}', in_rec[2], in_rec[3]

        t_list = list(IterReader(input_list).transform(TestReformat))

        self.assertEqual(t_list[0][0], 'Georgia-07')
        self.assertEqual(t_list[0][1], 'Green')
        self.assertEqual(t_list[0][2], 95.05)

    def test_transform_with_lambda(self):
        global input_list

        i = IterReader(input_list).transform(lambda r: (r[1], round(float(r[3]))))
        i_list = list(i)

        self.assertEqual(i_list[0][0], 'Georgia')
        self.assertEqual(i_list[0][1], 95)

    def test_transform_with_func(self):
        global input_list

        def rearrange(f):
            return f'{f[0][0:5]}-{f[0][5:8]}-{f[0][9:]}', f[2], f[1], f[4], f[3]

        i = IterReader(input_list).transform(rearrange)
        r = list(i)[0]

        self.assertEqual(r[0], '59693--IL-9641352')
        self.assertEqual(r[1], 'Green')
        self.assertEqual(r[2], 'Georgia')
        self.assertEqual(r[3], 7)
        self.assertEqual(r[4], 95.05)

    def test_transform_exception(self):
        global input_list

        i = IterReader(input_list).transform(Key)

        self.assertRaisesRegex(RuntimeError, "compatible only with a function or Reformat", list, i)


class TestReduceChainable(unittest.TestCase):

    def test_reduce_with_uniq(self):
        global input_list

        i = IterReader(input_list).cut(1).sort(0).reduce(Uniq, 0)

        expected = [
            ['Austria'],
            ['Sweden'],
            ['Georgia'],
            ['France'],
            ['Italy'],
            ['Malta'],
            ['Montenegro'],
            ['Norway'],
            ['Poland'],
            ['Spain'],
            ['Turkey'],
            ['Germany'],
            ['Ireland'],
        ]

        self.assertEqual(len(expected), len(i))

    def test_reduce_with_uniq_count(self):
        global input_list

        i = IterReader(input_list).cut(1, 2).sort(0, 1).reduce(UniqCount, 0, 1)

        self.assertEqual(len(i.filter(2, eq, 1)), 15)
        self.assertEqual(len(i.filter(2, eq, 2)), 3)
        self.assertEqual(len(i.filter(2, eq, 3)), 1)


if __name__ == '__main__':
    unittest.main()