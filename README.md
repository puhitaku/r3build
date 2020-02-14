r3build
=======

r3build _[rìːbíld]_ runs commands when you modify files.


Motivation
----------

I used to use [joh/when-changed](https://github.com/joh/when-changed). This is a handy tool to tell computers to do something when I make changes to files. But when it comes to complex detection, like "run make when I edit C code but ignore intermediate files," it won't fit or I had to write dirty grep filter to get rid of garbages.

To achieve complex detection, there should be a well-structured configuration file that describes its behavior. I've got an idea of r3build (detector with configuration file) and it came real finally.

