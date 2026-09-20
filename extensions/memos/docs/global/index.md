---
description: Use a Memos-compatible app as a capture interface for InKCre.
---

# Memos-compatible capture

The Memos Extension lets a compatible note-taking app connect directly to your InKCre instance.
InKCre provides the server; you do not need a separate Memos installation. Notes written through
that connection are saved in your InKCre information base.

This is a write-in interface, not a Source that fetches another Memos server. There is no Source,
collection Job, or Cron to create. It does not import existing notes from another service.

The current server implements a bounded subset of Memos 0.29.1. Its established compatibility
baseline is MoeMemos Android 2.0.4; this does not promise compatibility with every Memos client or
version. Unsupported server operations return errors rather than pretending to succeed.

To start, [connect your app](connect). You need a running InKCre instance, the Memos Extension,
and a Core address reachable from the device running the app.
