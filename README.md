r3build
=======

r3build _[rìːbíld]_ runs commands when you modify files.


Install
-------

r3build is not uploaded to PyPI yet. Please run the following command to install it.

```
$ pip install git+https://github.com/puhitaku/r3build
```


How to use (TL;DR version)
--------------------------

1. Write `r3build.toml` in your project directory.

```
$ cat r3build.toml
[[rule]]
name = "Build them all"
processor = "make"
only = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = "*~"
```

Not using `make`? Okay, here's a yet another general one.

```
$ cat r3build.toml
[[rule]]
name = "Run it"
processor = "command"
command = "python -m foobar"
only = ["modified"]
glob = ["./foobar/*.py", "./foobar/**/*.py"]
glob_exclude = "*~"
```

2. Invoke r3build. This watches what you edit.

```
$ python -m r3build
```

3. Edit your codes as you want, and enjoy them being built / run automatically.


How to use (verbose version)
----------------------------

The most important part of r3build, `r3build.toml`, defines how it watches, runs and builds the code.
Other than that, it also defines all behavior of r3build, like, how it outputs the logs to console.

Let's write your `r3build.toml` and place it into your project. It's good to put it in the root directory.

[The skeleton (template)](r3build.skeleton.toml) is placed in the root of this repository.

Here's an example of `r3build.toml` to run `make` every time you edit your C code:

```
[[rule]]
name = "Build them all"
processor = "make"
```

It's enough to watch your codes. But it'll be so annoying to you because it'll run make for ALL events
that occur to your codes -- when they are "created", "deleted", "moved" and "modified."

Here's an additional one to "filter" the events; the `only` key.

```
[[rule]]
name = "Build them all"
processor = "make"
only = ["modified"]
```

As a result, the rule will only be triggered when your codes are being edit (modified).
See [the skeleton](r3build.skeleton.toml) for the available values.

You'll notice that it triggers not only for `.c` and `.h` codes but all files.
It's super-easy to filter them only for `.c` and `.h` codes. Here's how:

```
[[rule]]
name = "Build them all"
processor = "make"
only = ["modified"]
glob = ["*.c", "*.h"]
```

You would already understood the most part of `r3build.toml`.
Here's one more to good to know. "Exclude" keys.

```
[[rule]]
name = "Build them all"
processor = "make"
only = ["modified"]
glob = ["*.c", "*.h"]
glob_exclude = "*~"
```

`*~` stands for the tilde files that Vim creates on saving.

For other processors and configurations, see [r3build.skeleton.toml](r3build.skeleton.toml) (and the code of course :wink:)


Motivation
----------

I used to use [joh/when-changed](https://github.com/joh/when-changed). This is a handy tool to tell computers to do something when I make changes to files. But when it comes to complex detection, like "run make when I edit C code but ignore intermediate files," it won't fit or I had to write dirty grep filter to get rid of garbages.

To achieve complex detection, there should be a well-structured configuration file that describes its behavior. I've got an idea of r3build (detector with configuration file) and it came real finally.


License and Copyright
---------------------

MIT License

Copyright (c) 2020 Takumi Sueda


