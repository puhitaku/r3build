<div align="center">
    <p><img width=500px src="./r3build.svg" alt="r3build logo"></p>
    <h1>r3build, a smart file watcher</h1>

[![CircleCI](https://circleci.com/gh/puhitaku/r3build.svg?style=svg)](https://circleci.com/gh/puhitaku/r3build) [![Coverage Status](https://coveralls.io/repos/github/puhitaku/r3build/badge.svg?branch=v1)](https://coveralls.io/github/puhitaku/r3build?branch=v1)
</div>


Preface
-------

r3build _[rìːbíld]_ is yet another smart file watcher that helps you develop something.
The most notable thing is the easy but powerful configuration system. It will enable you to install a
minimal watcher for the first step and also to grow the watcher to handle a wide range of file events.


Install
-------

r3build is not uploaded to PyPI yet. Please run the following command to install it.

```
$ pip install git+https://github.com/puhitaku/r3build
```


How to use (TL;DR)
------------------

1. Write `r3build.toml` in your project directory.

```
$ cat r3build.toml
[[target]]
name = "Build them all"
processor = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = ["extra/*", "extra/**/*"]
```

This means that "when .c or .h files are modified, run `make`, but ignore all files in `extra` directory."

Here's a yet another general one for who is not using `make`.

```
$ cat r3build.toml
[[target]]
name = "Run it"
processor = "command"
command = "python -m foobar"
when = ["modified"]
glob = ["./foobar/*.py", "./foobar/**/*.py"]
```

This means that "when Python code in `foobar` package is edited, run `__main__.py` in the package."

2. Invoke r3build. This watches what you edit.

```
$ python -m r3build
```

3. Edit your code as you want, and enjoy them being built / run automatically.


How to use (verbose)
--------------------

The configuration file, `r3build.toml`, defines how it watches, runs, and builds the code.
Other than that, it also defines all behavior of r3build like if it outputs the logs to console and how to filter events.
(For details, please refer to [the skeleton (template)](r3build.skeleton.toml) placed in the root of this repository.)

Here's an example of `r3build.toml` to run `make` every time you edit your C code:

```
[[target]]
name = "Build them all"
processor = "make"
```

The `[[target]]` line means that it's an item in `target` array. The `name` config means that the name of this `target` is "Build them all". The last `processor` config means that `make` processor will be invoked when this `target` gets triggered. `Processor` does not mean a shell command but a purpose-specific implementations for several types of build targets.

It's enough to get r3build watch your code. But it'll be annoying to you because it'll run `make` for ALL events
that occur to your code -- when they are "created", "deleted", "moved" and "modified."

Here's an additional one to "filter" the events; the `when` key.

```
[[target]]
name = "Build them all"
processor = "make"
when = ["modified"]
```

As a result, the target will only be triggered when your code is being edit (modified).
See [the skeleton](r3build.skeleton.toml) for the available values.

You'll notice that it triggers not only for `.c` and `.h` but all files.
It's super-easy to filter them only for `.c` and `.h` code. Here's how:

```
[[target]]
name = "Build them all"
processor = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
```

You would already understood the most part of `r3build.toml`.
Here's one more thing to good to know. "Exclude" keys.

```
[[target]]
name = "Build them all"
processor = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = ["extra/*", "extra/**/*"]
```

The `glob_exclude` configuration will ignore the changes occurred in `extra` directory.

For other processors and configurations, see [r3build.skeleton.toml](r3build.skeleton.toml) (and the code of course :wink:)


Confirmed platforms
-------------------

 - Python 3.8.3 + Debian Linux 10 (Buster)
 - Python 3.8.3 + macOS 10.14.6 Mojave

It should work on any platform with Python 3.6+.


Motivation
----------

I used to use [joh/when-changed](https://github.com/joh/when-changed). This was enough to watch changes. But when it comes to complex detection, like "run make when I edit C code but ignore intermediate files," I had to write dirty grep filter to get rid of garbages.

To achieve the smart detection, I thought of a well-structured configuration file that describes its behavior and finally I got the concept of r3build.


License and Copyright
---------------------

MIT License

Copyright (c) 2020 Takumi Sueda

