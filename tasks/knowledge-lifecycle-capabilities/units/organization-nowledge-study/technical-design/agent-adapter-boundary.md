# Agent Definition Selection Correction

- **状态**：D-501 closed；先前的 run-time Tool policy proposal 已撤回。
- **作用**：保留错误因果链和修正，避免后续再次把 Agent definition 当成不完整配置。

## 错误

先前从“Agent definition 可能误带不适合当前模型的 Tool”推出：

```python
AgentManager.run(..., required_tools=..., allowed_tools=...)
```

这把普通配置错误虚构成新的 runtime boundary，并制造了第二份 Tool authority。

## 修正

Agent definition 已经完整选择：

```text
system prompt + AI model + exact Tool IDs + tool choice + per-turn budget
```

系统可以持久化多个 definitions。Evolution、synthesis、existing-referent anchoring 和 duplicate assertion 的执行路径
分别选择为该场景组成的 definition；不希望 Agent 拥有的 Tool 不出现在该 definition 中即可。

```text
exact execution family
  -> select purpose-built Agent definition
     -> AgentManager binds that definition exactly
        -> shared read Tools + exact mutation Tool(s)
```

`AgentManager` 不增加 allowlist、required set、Tool override 或 Organization-specific policy。精确 Organization command
继续不 import Agent；AgentManager 也不理解 Organization semantics。

## 保留的独立结论

Agent Thread 的 ToolCall/ToolResult history 只服务于本次 Agent 推理，不反向成为 Job 的数据合同。D-518 进一步确认：
Job 不读取 Thread，也不汇总 BehaviorReport；graph、JobStatus 与结构化日志分别承担持久效果、生命周期和过程诊断。
