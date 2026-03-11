---
layout: default
title: hottakes
---
# Hot Chilly Takes

{% for take in site.takes reversed %}
[{{ take.title }}]({{ take.url }})

{{ take.excerpt }}
{% endfor %}