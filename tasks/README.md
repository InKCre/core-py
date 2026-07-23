# Tasks

This directory is the Spoke-local, agent-owned task workspace of the repository.

Every non-trivial task packet must include these MVT anchors:

- Objective & Hypothesis
- Guardrails Touched
- Verification

Keep a compact, human-inspectable control surface with:

- Current Understanding
- User-Confirmed Constraints
- Active Mode or Transition Note
- Next Step

Use this directory for:

- local exploration before durable promotion
- diagnostics before bug fixes
- transient artifacts and one-off execution notes
- temporary reasoning that should not pollute durable docs
- evidence and human-agent collaboration state
- local-pressure capture before promoting a missing shared rule into the Hub repo

Do not treat files here as permanent truth.

A task packet may start as one file. Move it to `tasks/<task-id>/packet.md` and split adjacent notes, evidence, decisions, verification, or temporary work only when collaboration pressure makes the compact form harder to inspect.

Exclude `tasks/` from ordinary source and durable-doc search unless the active question targets task state or evidence.

Promote only stable, reusable, expensive-to-rediscover knowledge into durable docs, and keep the owning layer explicit.
