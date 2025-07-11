---
layout: default
title: home
---

# bitboy.ro

## hei,

i am Roman Botnari, a developer from Romania.
i work for Axway on a platform for secure and reliable data exchanges.

bitboy.ro is the place where I investigate technologies, publish experiments, personal projects and share hot tokes 🌶️.

## techstack
I speak Java (i know.. 🦙) with a Spring Boot dialect, some Python, Javascript,

and I'm able to mimic any other language that has a tutorial or repo that compiles without errors in my 🌍 environment.

To construct my experiments I use a variety of tools and technologies, including:
* databases (relational, vector, etc.)
* containers (Docker, Kubernetes)
* and of course (the infamous) prompt engineering.

## ai
artificial intelligence is the hottest 🔥 topic of the moment, so in the upcoming articles I will explore this goldmine 🧈🏃🏻.

## Last posts
{% for post in site.posts reversed limit:3 %}
[{{ post.date | date_to_string }} - {{ post.title }}]({{ post.url }})
{% endfor %}

## Last hottakes
{% for take in site.takes reversed limit:3 %}
[{{ take.title }}]({{ take.url }})
{% endfor %}