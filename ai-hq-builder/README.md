# AI HQ Builder — scratch workspace

Scratch workspace for AI HQ Builder deliverables. Not application code. Safe to delete.
Owner: AI HQ program.

This directory is a **staging area for returned Builder deliverables only**. It is **not**
the `ai-hq` repository and must never be treated as the authoritative baseline. The pinned
export snapshot remains the build input; files land here so they can be handed to Fable,
who performs all branch/PR/merge mechanics.

Nothing outside `ai-hq-builder/` is written by the Builder.

```
ai-hq-builder/
  README.md                     <- this file
  task-0002/
    returned/                   <- complete copies of changed files (packet-relative paths)
    BUILDER_DELIVERY_RECORD.md
```

Per APP-09 (two-lane trust-boundary invariant) the Builder holds no `ai-hq` credentials.
