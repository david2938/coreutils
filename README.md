# coreutils

Coreutils is a fluent interface inspired by time-honored Unix command-line utilities like cut, sort and grep

## Description

I recently needed to solve an ETL problem using some very difficult data files.  I found myself turning to my 
old standbys, the Unix command-line utilities available on every flavor and version of Unix I have ever encountered.  
Using `sort`, `uniq`, `cut`, `grep`, and `sed`, you can transform almost any data.  And when you need more of a 
programming environment, `awk` typically has just enough functionality to handle most tasks that are too hard to
specify in `sed`.  There were a few parts, though, that needed some serious programming at which point I lamented
that there isn't a similar way to chain simple functions together in Python so that the easy things can be done
quickly, and the hard things can be handled with actual Python.  Thus was born the idea of "coreutils".

Coreutils is based as much as possible on Python's iterator and generator capabilities.  This makes the module
memory efficient and delays evaluation of any combination of functions until data needs to be materialized.

Chains of utilities can be shared and used in multiple ways, and as much as possible, they can be substituted
directly into all standard Python functions that accept an iterator.  Additionally, `coreutils` can consume any
iterator.  This makes it very easy to integrate `coreutils` into logic that also uses other modules, libraries
and frameworks.

## Installation

Currently coreutils is just a module.  Download it and include it in your project directory.

Depending on the structure of your project, you may need to create an "__init__.py" file.

### Python Compatibility

Currently coreutils only works with Python 3.  A version-agnostic update will be released very soon.

## Docuentation

Currently just this readme file, but planning on publishing in-depth documentation on readthedocs.io

### Examples

The best place to start looking at examples is the unit tests file `test_coreutils.py`

## License

Use of coreutils is granted under the terms of the [MIT License](./LICENSE).
