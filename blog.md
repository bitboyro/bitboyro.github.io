---
layout: default
title: blog
---
# Last posts

{% for post in site.posts %}
[{{ post.title }}]({{ post.url }})

{% endfor %}