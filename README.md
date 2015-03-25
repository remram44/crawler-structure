What is this?
=============

This is the basic structure for a web crawler. It doesn't actually crawl, but everything is there to add it -- you just need to select new links from a page to download. However I'm not interested in doing that right now, so it's not there.

What *is* there is a way to start a crawler instance and update the HTML page with new result dynamically (over a websocket). There is also code to perform a search with the [Bing API](http://www.bing.com/dev/en-us/dev-center).

This code uses the [Twisted framework](https://twistedmatrix.com/), an asynchronous network engine which allows it to perform many requests in parallel, to serve the website and to communicate on websockets. The websocket protocol implementation comes from [Autobahn](http://autobahn.ws/).

Why?
====

Mainly wanted to try Twisted, but I'm not interested in the HTML handling & classification problems. However I might add that later on if I feel like it.
