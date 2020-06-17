<div align="center">
    <p><img width=400px src="./r3build.svg" alt="r3build logo"></p>
    <h1>r3build, a smart file watcher</h1>

[![CircleCI](https://circleci.com/gh/puhitaku/r3build.svg?style=svg)](https://circleci.com/gh/puhitaku/r3build) [![Coverage Status](https://coveralls.io/repos/github/puhitaku/r3build/badge.svg?branch=v1)](https://coveralls.io/github/puhitaku/r3build?branch=v1)
</div>


Preface
-------

r3build _[rìːbíld]_ is yet another smart file watcher that helps you develop something.
The most notable thing is the simple and powerful configuration system. It will enable you to install a
minimal watcher for the first step and also to grow the watcher to handle a wide range of file events.


Install
-------

```
$ pip install r3build
```


How to use (Case 1: one-shot build)
-----------------------------------

The first one introduces a combination of simple event detection and a "one-shot" task.
When you edit your code and save it, r3build invokes a make target detecting that file event.

1. Write `r3build.toml` in your project directory.

```
$ cat r3build.toml
[[job]]
name = "Build them all"
type = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = ["extra/*", "extra/**/*"]
```

This means that "when .c or .h files are modified, run `make`, but ignore all files in `extra` directory."

Another example:

```
$ cat r3build.toml
[[job]]
name = "Run it"
type = "command"
command = "python -m foobar"
when = ["modified"]
glob = ["./foobar/*.py", "./foobar/**/*.py"]
```

This means that "when a Python code in `foobar` package is edited, run `__main__.py` in the package."

2. Invoke r3build. This watches what you edit.

```
$ r3build
```

Alternatively:

```
$ python -m r3build
```

3. Edit your code as you want, and enjoy them being built / run automatically.


How to use (Case 2: auto-reloading)
-----------------------------------

Let me introduce "auto-reloading" use-case for the second one.

Say you're building a great asynchronous system with [Celery](https://github.com/celery/celery/).
While the most popular way to reload Celery is to use [watchdog](https://github.com/gorakhargosh/watchdog),
r3build has advantages to it;

 - No longer have to write one-liners and double-hyphens
 - Manage all auto-reload tasks in one place

Not only Celery, r3build is capable of restarting any process of course.

1. Write `r3build.toml` in your project directory.

```
$ cat r3build.toml
[[job]]
name = "Run celery"
type = "daemon"
command = "celery worker --app=app.entrypoint"
when = ["created", "modified"]
regex = ".+\.py$"
```

This means that:
 - r3build launches Celery as a child process
 - When .py files are created or modified, restart already running Celery

Suppressing std* is also available.

```
$ cat r3build.toml
[[job]]
name = "Run celery"
type = "daemon"
command = "celery worker --app=app.entrypoint"
when = ["created", "modified"]
regex = ".+\.py$"
stdout = false
stderr = true
```

2. Invoke r3build.

```
$ r3build
```

3. Watch it restart as you write code. Voila!


How to use (verbose)
--------------------

The configuration file, `r3build.toml`, defines how it watches, runs, and builds the code.
Other than that, it also defines all behavior of r3build like if it outputs the logs to console and how to filter events.
(For details, please refer to [the skeleton (template)](r3build.skeleton.toml) placed in the root of this repository.)

Here's an example of `r3build.toml` to run `make` every time you edit your C code:

```
[[job]]
name = "Build them all"
type = "make"
```

The `[[job]]` line means that it's an item in `job` array. The `name` config means that the name of this `job` is "Build them all". The last `type` config means that this job invokes `make` command when this it gets triggered.

The example is enough for r3build to watch your code while it'll accept ALL file events
that occur to your code -- when they are "created", "deleted", "moved" and "modified".

Here's an additional example to "filter" the events; the `when` key.

```
[[job]]
name = "Build them all"
type = "make"
when = ["modified"]
```

As a result, the job will only be triggered when your code is being edit (modified).
See [the skeleton](r3build.skeleton.toml) for the available values.

You'll notice that it triggers not only for `.c` and `.h` but all files.
It's super-easy to filter them only for `.c` and `.h` code. Here's how:

```
[[job]]
name = "Build them all"
type = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
```

You would already understood the most part of `r3build.toml`.
Here's one more thing to good to know. "Exclude" keys.

```
[[job]]
name = "Build them all"
type = "make"
when = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = ["extra/*", "extra/**/*"]
```

The `glob_exclude` configuration will ignore the changes occurred in `extra` directory.


Spec of r3build.toml
--------------------

See [r3build.skeleton.toml](r3build.skeleton.toml) for available configurations.

The full example of r3build.toml is not yet described but simpler examples are in [examples](examples).


Environment variables
---------------------

Following variables are added when jobs get launched. See [examples](examples) for usage.

 - `$R3_EVENT`: event type
    - `moved`
    - `deleted`
    - `created`
    - `modified`
 - `$R3_FILENAME`: file name
 - `$R3_IS_DIRECTORY`: if it's a directory or not
    - `0`: Not directory
    - `1`: Directory


Q&A
---

#### Q. I wrote regex rules but nothing happens even it's modified... How to debug it?

Enabling Verbose mode with `-v` flag or enabling all logs will provide a way to analyze it.

```
$ r3build -v
```

```
[log]
all = true
```

`-v` and `log.all = true` are equivalent.

#### Q. Where are the specs of regex and glob rules?

We use [`re` package](https://docs.python.org/ja/3/library/re.html) for regex
and [`fnmatchcase()` from `fnmatch` package](https://docs.python.org/ja/3/library/fnmatch.html#fnmatch.fnmatchcase)
for glob. Please refer those documents.

#### Q. Can I merge r3build.toml and pyproject.toml or any other TOML documents?

Yes, it should be possible if the keys in document root don't collide with the another document.
r3build doesn't care other than `log`, `event`, and `job` keys.

Confirmed platforms
-------------------

 - Python 3.8.3 + Debian Linux 10 (Buster)
 - Python 3.8.3 + macOS 10.14.6 Mojave
 - Python 3.8.3 + macOS 10.15.4 Catalina

It should work on any platform with Python 3.7+.


Motivation
----------

I used to use [joh/when-changed](https://github.com/joh/when-changed). This was enough to watch changes. But when it comes to complex detection, like "run make when I edit C code but ignore intermediate files," I had to write dirty grep filter to get rid of garbages.

To achieve the smart detection, I thought of a well-structured configuration file that describes its behavior and finally I got the concept of r3build.


Contribute
----------

See [here](CONTRIBUTING.md) for contribution rules.


License and Copyright
---------------------

MIT License

Copyright (c) 2020 Takumi Sueda

