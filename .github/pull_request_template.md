<!--
Fill in every heading below. A heading with nothing under it is an unanswered
question, not a heading that does not apply. Where something genuinely does not
apply, say that and say why.
-->

## What this changes

<!-- One topic. A change carrying two unrelated topics has a description of one
of them. -->

## Which issue it closes

<!-- Closes #NNN. Every change starts as an issue. If there is no issue, open
one first and say there what is wrong, what the evidence is, and what done
means. -->

## What failure it prevents

<!-- The failure this change makes impossible, or less likely. Where a guard is
added, say what it refuses and how the refusal was shown to bite: the guard is
proven by removing it and watching the check go red, not by asserting that it
would. -->

## The means check

<!-- One sentence naming the means this change is made of, the language, the
format, the tool or the runtime, and the reason it fits. Every time, and never
carried over from the last change, because a means that was right there is an
assumption about this one. Where the change adds no new means, say which
existing one it uses. -->

## Commands behind every claim

<!-- Every number and every assertion above carries the command that produced
it, run at the commit being pushed and against the reference a reader will have
rather than against your working tree. Paste the command and its output. Where a
claim cannot be backed by a command, write it as a claim and say so. -->

```
```

## What was not done

<!-- What this change deliberately leaves out, what is untested, and what is
assumed rather than measured. A negative disclosure stays negative: if something
was not run, this section says it was not run. -->

---

<!--
Sign your commits off. Every non-merge commit needs a Signed-off-by trailer that
matches its author, which `git commit -s` adds and `git rebase --signoff <base>`
adds retroactively. What you are asserting by adding it is in ./DCO.
-->
