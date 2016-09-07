# feedreader

Commandline RSS and Atom client


# Installation

1. clone this repository
1. `pip install -e .`


# Usage

```bash
feedreader --help
```

# Example


Read a [Lorem RSS](http://lorem-rss.herokuapp.com/) feed:

```
$ feedreader --interval 10 'http://lorem-rss.herokuapp.com/feed?unit=second&interval=5'
2016-09-06 12:02:20+00:00
Feed<url='http://lorem-rss.herokuapp.com/feed?unit=second&interval=5', interval=10>
   Lorem ipsum 2016-09-06T12:02:20+00:00
   http://example.com/test/1473163340

2016-09-06 12:02:25+00:00
Feed<url='http://lorem-rss.herokuapp.com/feed?unit=second&interval=5', interval=10>
   Lorem ipsum 2016-09-06T12:02:25+00:00
   http://example.com/test/1473163345

2016-09-06 12:02:30+00:00
Feed<url='http://lorem-rss.herokuapp.com/feed?unit=second&interval=5', interval=10>
   Lorem ipsum 2016-09-06T12:02:30+00:00
   http://example.com/test/1473163350

2016-09-06 12:02:35+00:00
Feed<url='http://lorem-rss.herokuapp.com/feed?unit=second&interval=5', interval=10>
   Lorem ipsum 2016-09-06T12:02:35+00:00
   http://example.com/test/1473163355

...
```