# Ingest run lifecycle state

## Summary

**Context:** Gmail ingest should start exactly one assistant run for each new message in a Gmail thread while avoiding duplicate drafts or side effects.

**Problem:** Scheduled and manual ingest both record the Gmail message ID in thread metadata before the processing run is safely durable or handled.

**Impact:** If the metadata write succeeds and run creation or the run itself fails, later automatic ingest can treat the message as already processed and skip the retry path.

**Recommendation:** Separate in-progress state from completed or pending-review state so ingest can retry stale failures without duplicating active human-review work.

## Evidence

- [scheduled ingest](https://github.com/rolandgvc/executive-ai-assistant/blob/main/eaia/cron_graph.py#L35-L48) skips a matching `email_id`, then writes that same metadata before creating the `main` run.
- [manual ingest](https://github.com/rolandgvc/executive-ai-assistant/blob/main/scripts/run_ingest.py#L63-L82) has the same update-before-run-create sequence; with the default early mode, a matching ID stops the scan.

## What I Found

The current metadata key acts as both a dedupe marker and an implied completion marker. That is safe only if the run is created and reaches a handled state every time after the metadata write. The graph has legitimate long-running states, especially pending Agent Inbox review, so a safe fix should distinguish active pending work from failed or completed work.

## Options

| Option | What changes | Pros | Cons |
| ------ | ------------ | ---- | ---- |
| A | Move the `email_id` metadata update after `runs.create` succeeds. | Smallest patch; prevents lost emails when run creation itself fails. | Still suppresses retry if the created run later fails before handoff or completion. |
| B | Add lifecycle metadata such as `processing_email_id`, `processing_run_id`, `processing_started_at`, `completed_email_id`, and `status`. | Handles run-create failures, stale in-progress runs, completion, and pending human review explicitly. | Requires updating ingest and terminal/pending graph paths together. |
| C | Query LangGraph run state for the thread before skipping a matching email. | Avoids new metadata fields and can detect failed runs. | Couples ingest to run-list semantics and still needs a policy for pending human-review runs. |

## Recommended Plan

1. Implement option B for both scheduled and manual ingest.
2. Treat active pending-human-review runs as not retryable, but treat stale or failed in-progress runs as needing retry or operator surfacing.
3. Mark `completed_email_id` only after terminal handled paths such as mark-read or approved side-effect completion, and record a pending-review status when an interrupt is created.
4. Keep the manual `--rerun` path able to override lifecycle metadata for explicit operator recovery.

## Acceptance Criteria

- [ ] Issue <project_issue id="019dc8db-c999-7260-9f92-b357b892ad23" /> is linked to this PR.
- [ ] Scheduled and manual ingest no longer use one metadata field as both started and completed state.
- [ ] A run creation failure does not mark the Gmail message complete.
- [ ] Pending human review is preserved without spawning duplicate drafts or side effects.
- [ ] Stale or failed in-progress work has a retry or operator-visible recovery path.
