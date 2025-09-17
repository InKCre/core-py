---
applyTo: '**/*.py'
---

- 在 None 也是有效值的地方使用 Undefined 替代 None 原本的语义。
  - `from pydantic_core import PydanticUndefinedType as UndefinedT, PydanticUndefined as Undefined`
`
