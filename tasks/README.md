# Tasks

This directory is the Spoke-local, agent-owned task workspace of the repository.

Every non-trivial task starts with one `packet.md`. Keep its compact,
Human-facing control surface sufficient to recover:

- the outcome and material guardrails
- the terminal claim and how it will be verified
- consequential current truth, decisions, and uncertainty
- the current front or next step at useful resolution
- one Human attention item, only when one exists

Use the installed v14 corpus when guidance is needed:

```bash
svc lookup --path index.md
svc lookup --path task-packet/index.md
svc task init <task-id>
svc task grow <task-id>
```

`svc task init` creates only `packet.md`. `svc task grow` is read-only and
reports shape; it does not decide topology or edit files.

Use this directory for:

- local exploration before durable promotion
- diagnostics before bug fixes
- transient artifacts and one-off execution notes
- temporary reasoning that should not pollute durable docs
- evidence and human-agent collaboration state
- local-pressure capture before promoting a missing shared rule into the Hub repo

Do not treat files here as permanent truth. A Task Packet owns only task-local
state whose persistence, recovery, or sharing lowers coordination cost; it does
not own durable project truth, Working Methods, acceptance, or a runtime work
graph.

A task packet may start as one file. Split adjacent Plans, Cells, Inquiries,
Designs, Decisions, Diagnostic Matrices, or Verification material only when a
distinct owner and real topology, retrieval, or coordination pressure make the
package cheaper to control. Supporting files are opt-in, not mandatory
scaffolding or a completed-work log.

Exclude `tasks/` from ordinary source and durable-doc search unless the active question targets task state or evidence.

Update the semantic information owner first, then task work-control state, then
the short Human projection. Promote only stable, reusable,
expensive-to-rediscover knowledge into durable docs, and keep the owning layer
explicit. At close, check for stranded deltas and material residual; do not
perform an archive or deletion-time promotion ceremony.
