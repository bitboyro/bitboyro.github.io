---
layout: default
title: blog
---
# Last articles

{% for article in site.articles reversed %}
[{{ article.title }}]({{ article.url }})

{% endfor %}