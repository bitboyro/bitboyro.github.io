---
layout: default
title: blog
---
# Last posts

{% for post in site.posts reversed %}
[{{ post.title }}]({{ post.url }})

{% endfor %}