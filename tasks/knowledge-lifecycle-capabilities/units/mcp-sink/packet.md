# MCP Sink

- **State**: Active — Product discussion。
- **Objective**: make InKCre available to external Agents through MCP as the first sink vertical。
- **Product boundary**: MCP serves **Agent retrieval of InKCre**。The downstream Agent owns whether retrieved information is
  used for writing、design、coding、chat or another task。
- **Non-goals**: generic sink framework、IME/browser/Figma/ChatGPT-specific sink、answer generation、Chat InKCre、hybrid
  retrieval composition。
- **Current premise**: info-base query primitives now exist：feature/lexical retrieval、semantic retrieval and graph-navigation
  retrieval。MCP should expose useful access to those primitives and solved content without becoming their owner。
- **Next discussion surface**: decide the minimal MCP tool surface and result contract for Agent use，then derive technical
  topology、acceptance and implementation plan。

## Delivery Gate

```text
Product contract
  → Technical contract ↔ Acceptance draft ↔ Implementation-plan probe
  → evidence preflight / branch simulation
  → Impact Handshake
  → explicit “开始”
  → Execute
  → Verify / Promote
```

No implementation is authorized by this packet。
