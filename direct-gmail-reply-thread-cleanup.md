# Direct Gmail reply thread cleanup

## Summary

**Context:** The assistant should clear pending Agent Inbox review work when the executive replies directly in Gmail instead of acting through the review UI.

**Problem:** Ingest detects direct Gmail replies, but it derives the LangGraph thread to close from the current Gmail message ID; when that message is not the original inbound email that created the review run, the close signal can target a different or missing thread.

**Impact:** Reviewers can see stale Agent Inbox items for emails the executive has already handled directly.

**Recommendation:** Move the cleanup identity to the Gmail thread, either by deriving LangGraph thread IDs from Gmail thread IDs for new runs or by adding a lookup from Gmail thread metadata to the active review thread before ending it.

## Evidence

- [Conversation ID derivation](https://github.com/rolandgvc/executive-ai-assistant/blob/main/eaia/conversation.py#L6-L8) currently keys LangGraph threads from `email['id']`.
- [Scheduled ingest](https://github.com/rolandgvc/executive-ai-assistant/blob/main/eaia/cron_graph.py#L21-L34) applies `user_respond` cleanup to only that derived thread and skips if it is not found.
- [Gmail fetch](https://github.com/rolandgvc/executive-ai-assistant/blob/main/eaia/gmail.py#L241-L246) emits `user_respond` rows for matching Gmail messages in a thread whose latest message is from the user.

## What I Found

The system already has the right high-level behavior: user-authored Gmail replies should end the assistant workflow instead of leaving review work open. The weak point is identity. A pending review run is tied to the inbound message that created it, while the later direct reply can be represented as a different Gmail message in the same Gmail thread.

## Options

| Option | What changes | Pros | Cons |
| ------ | ------------ | ---- | ---- |
| A | Derive LangGraph thread IDs from Gmail `thread_id` instead of message `id` for all new ingests. | Simple model; direct replies and follow-ups naturally resolve to the same thread. | Needs a migration/compatibility decision for existing message-keyed threads. |
| B | Keep message-keyed runs, but store and search an active-review mapping by Gmail `thread_id` when `user_respond` is detected. | Lower migration risk; preserves current per-message run identity. | Requires a reliable metadata lookup path and cleanup when runs complete. |
| C | Emit both the current message-derived ID and Gmail-thread ID, trying both during cleanup. | Minimal code change for future thread-keyed runs. | Does not close older message-keyed runs unless the original message ID is still in the fetched result set. |

## Recommended Plan

1. Choose whether new work should be keyed by Gmail thread or whether per-message run identity is required.
2. If Gmail-thread identity is acceptable, update `conversation_id_for_email` to use `email['thread_id']`, add a compatibility note for existing runs, and update stale index/docs that describe the mapping.
3. If per-message identity must stay, add an active-review lookup keyed by Gmail `thread_id` and use it in both scheduled and manual ingest before skipping `user_respond` rows.
4. Add a small unit test for a direct reply represented by a different Gmail message ID than the original inbound message.

## Acceptance Criteria

- [ ] Direct Gmail replies close the active review thread for the Gmail thread, not just a thread derived from the reply message ID.
- [ ] Scheduled and manual ingest use the same cleanup behavior.
- [ ] Existing active runs have a documented compatibility path or migration choice.
- [ ] The linked issue is updated with the selected implementation approach.
