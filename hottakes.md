---
layout: default
title: hottakes
---
# Hot Chilly Takes

{% assign latest_takes = site.takes | sort: 'date' | reverse %}
{% for take in latest_takes %}
[{{ take.title }}]({{ take.url }})

{{ take.excerpt }}
{% endfor %}