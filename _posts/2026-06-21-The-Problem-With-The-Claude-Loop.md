---
layout: post
title: The Problem With Claude Code's /loop
description: I gave Claude Code's Loop a spin. Here are the problems I ran into — and why "run this prompt on repeat" is more nuanced than it sounds.
toc: true
---

# The premise

Geoffrey Huntley with [everything is a ralph loop](https://ghuntley.com/loop/) and Boris Cherny during his [many conferences](https://youtu.be/SlGRN8jh2RI?si=PE82wMdAIZnaYEYV) popularized the idea of iterative, autonomous AI coding loops.

The pitch is good. You hand Claude a prompt, say "do this again and again," then walk away from the computer. Come back to a finished mountain of work. ⛰️

That's the dream. The Loop is the closest thing Claude Code has to it. Or is it? 

The hype around this is big, so I put on my tester cap and ran some experiments.

This isn't a takedown — it's a field report. The Loop is genuinely a useful idea, but the implementation can be improved.

<img class="resize" src="/assets/images/claude_loops/claudeloopsmeme.jpg" alt="claudeloopsmeme.jpg"
  style="width:100%;max-width:900px;display:block;"
/>

## What is it though?

It's a function you can call from Claude Code via `/loop`.

```shell
/loop 5m check if the deployment finished and tell me what happened
```


The Loop runs a prompt on repeat. Each iteration, Claude does the work, and then goes around again. No babysitting, no copy-pasting the same instruction into the box every two minutes.

In theory you set it loose and it grinds.

In practice, you're handing the keys to something that can't see the odometer. Let me explain.

# The 99 problems but a loop ain't one

## Can't stop (the loop), addicted to the shindig

The first thing you need to learn about the Loop is how to get out of it.

And it's not easy.

The official documentation says to [press ESC](https://code.claude.com/docs/en/scheduled-tasks#stop-a-loop), but that failed for some of my loops.

You can also [ask Claude in natural language](https://code.claude.com/docs/en/scheduled-tasks#manage-scheduled-tasks) to cancel the job, which didn't work every time. I'd cancel a task then minutes later watch a new iteration start.

Under the hood, Claude uses these tools:

* CronCreate
* CronList
* CronDelete

But we don't have direct access to these.

What worked for me reliably thus far was stopping the session completely.

Once it's spinning, there's no clean **stop** button that says "finish what you're doing and stand down." Your reliable exit is to close the session — a sledgehammer when you wanted a brake pedal.

## You can't watch it

Here's the part that bothered me most.

You can't monitor the loop.

You can *ask* Claude to write down its state each iteration — keep a little log, a counter, a status file. Sounds reasonable. And it works, right up until it doesn't, because the bookkeeping is done by the same thing you're trying to keep an eye on. 👀

It's like asking someone to grade their own homework, mid-exam, every five minutes, without ever looking up.

## Claude doesn't know where it is

This is the root of it.

Claude is unaware of the state of the loop.

It doesn't have a reliable, privileged view of "I am on iteration 7 of 20." From inside, every turn looks a lot like the last one. So when you ask "how's it going?", the answer isn't a readout. It's a guess dressed up as a readout.

Which means it can — cheerfully, confidently — **lie to you about the work it's doing.** Not out of malice. Out of not knowing. ⚠️

Large language models are confident beasts. They'll tell you a tidy story before they'll tell you `I'm not sure`.

## No memory management

The Loop doesn't optimize how it spends tokens.

There's no clever memory system trimming the fat between iterations, summarizing what's done, keeping only what matters. Instead it just reuses the session context. The same growing pile, dragged forward, turn after turn.

So the longer the loop runs, the heavier each iteration gets. You're not running the same lap twenty times — you're running it carrying everything from all the laps before. 🎒

This is the quiet tax. It doesn't announce itself. It just makes the back half of a long loop slower, fuzzier, and pricier than the front half.

## It doesn't do what you said

And then there's plain unreliability.

The Loop or Claude Code in general will happily color outside the lines of its own instructions.

My favorite example. I told it: **invent one spy name each iteration.** 🕵️

Simple. One name. Every time.

- Iteration one: it invented **two**.
- Iteration two: **four**.
- Iteration three: back to **one**.

No pattern. No drift I could explain. Just a coin flip wearing the costume of a deterministic process.

Now scale that. If it can't reliably produce *one spy name on command*, what is it quietly miscounting in the work you care about?

# So what is the /loop good for?

I don't want to leave it here, because the Loop isn't useless. It's powerful in exactly the cases where its weaknesses don't bite:

- **Tasks that are independently verifiable.** If each iteration produces something you can check afterwards — a file, a test result, a diff — the lying problem shrinks. You don't have to trust the narration; you can read the output.
- **Tasks that are tolerant of variance.** If "two spy names instead of one" wouldn't ruin your day, the unreliability is noise, not poison.
- **Short loops.** The memory tax and the drift both compound with length. Keep it short and you stay on the good half of the curve.

The Loop is a power tool, not an autopilot. Treat it like one that's missing a few safety guards.

# The Loop lives and dies by the session

Here's a structural thing that's easy to miss until it bites you.

The Loop is a **session concept**. It lives inside your open Claude Code conversation. Close the terminal, exit the session, lose the SSH connection — and the loop is gone with it. There's nothing running on a server somewhere, faithfully grinding while you sleep. The "autonomy" only lasts as long as you keep the window open. 🪟

That's fine for "poll this deploy for the next twenty minutes." It's useless for "do this every morning at nine, whether or not my laptop is awake."

Which brings me to the alternatives.

## Alternative 1: schedule it in the cloud with Routines

Claude Code can also run prompts on a schedule that *isn't* tied to your session. The docs call these [routines](https://code.claude.com/docs/en/routines).

The difference is the whole point:

- **The Loop runs on your machine, in your session.** Machine off or session closed → nothing happens.
- **A cloud routine runs on Anthropic's infrastructure.** Your machine can be off. There's no open session to babysit. It fires on its cron and runs autonomously. ☁️

The trade-offs flip too. A cloud routine works from a **fresh clone**, so it has no access to your local files and no inherited session context. It runs at most once an hour. And it runs without permission prompts — which is what you want for unattended work, and what you should be nervous about if the prompt is vague.

So: cloud routines solve the "dies with the session" problem outright. They don't automatically solve the *monitoring* and *context* problems — for that, sometimes you want to go fully DIY.

## Alternative 2: roll your own cron with Agent SDK

Here's the move I keep coming back to. Forget the built-in loop entirely. Write a real cron job that calls Claude in headless mode:

```bash
# crontab -e
0 9 * * *  cd ~/project && claude -p "review yesterday's commits and summarize regressions" >> ~/claude-cron.log 2>&1
```

`claude -p "...do this"` runs Claude Code non-interactively: one prompt in, one result out, then it exits. No session to hold open. The OS scheduler — the same boring, battle-tested cron that's been running the internet for decades — decides when it fires.

You manage the plumbing yourself. That's the cost. But look at what you buy:

- **Fresh context every run.** Each invocation starts clean. No reused session pile dragging forward, no quiet token tax compounding over the back half.
- **Real monitoring.** The run writes to a log file. To stdout. To a status endpoint, a Slack webhook, a database row — whatever you wire up. The bookkeeping is done by *your* code, outside the model, so it can't be fudged by the thing it's watching. 👀
- **A real stop button.** Want it to stop? Remove the cron line. Want to pause? Comment it out. No `/rewind`, no panic button.
- **Composability.** It's just a shell command. Pipe it, gate it behind a condition, chain it after a build, retry it, alert on a non-zero exit. It behaves like every other Unix tool because it *is* one.

The honest catch: you're now responsible for the scaffolding. Cron syntax, logging, error handling, making sure the working directory and auth are right. The Loop hands you convenience and takes your control. The DIY cron hands you control and takes your convenience.

And there's a budget catch too. `claude -p` uses the same engine as the [Agent SDK](https://code.claude.com/docs/en/headless), and an unattended cron run needs credentials that work without a human at the keyboard — in practice, an `ANTHROPIC_API_KEY` with usage budget on it (bare mode skips the OAuth/keychain path entirely and *requires* the API key). Every fire burns tokens against that budget, so a cron firing every five minutes is a cron spending money every five minutes whether or not there was anything to do. 💸

For anything I want running unattended, I'll take the control.

# The takeaway

The Loop sells you autonomy. What it actually gives you is *unsupervised token consumption*, which is a different thing.
The gap between those two is filled by everything I've described: no clean stop, no real monitoring, no self-awareness, no memory hygiene, no guarantee it follows its own brief.

None of that makes it bad. It makes it a tool with sharp edges — and worth knowing where they are before you grab it. When the edges start cutting, you have somewhere to go: a cloud routine for things that must run without you, or a plain old cron calling `claude -p` when you want full control over context and visibility.

Use the Loop for what it's good at — quick, supervised, in-session repetition. Reach for the others the moment "unattended" or "I need to trust this" enters the picture.

Compile your loops wisely. 🔁