# 端到端黑盒语料与观察

- **状态**：D-525 accepted initial corpus；具体 fixture wording/content 在 Implementation Plan/implementation 中形成。
- **目的**：用少量 realistic information worlds 观察整组自动 Organization 是否产生可复用图区别；不是为每个内部机制
  建立一项测试，也不声称穷尽语义空间。

## Corpus 原则

每个 world 由普通 information、provenance 和已有关系组成，包含相互交织的真实需要，而不是预先标注“请运行
supersession/synthesis”的独立测试句子。整体应覆盖：

- 同一对象在不同时间、scope 与 authority 下的变化；
- 互补、冲突和复制传播的多来源信息；
- composite Block、隐含指称、同名对象和 material detail；
- 与目标主题相似但不应产生关系的 distractors；
- 至少一个关键依据位于 initial seed/一跳邻域之外；
- 至少一个行为发现另一个行为更适合处理的粒度或前置组织机会；
- 后续能够实际使用 current/history、source basis、referent path 或 duplicate component 的请求。

Corpus manifest 只保存来源、测试别名和 Human 用来理解 world 的背景；不向被测系统暴露 expected behavior、pair、source
set、selected fragment 或 relation。别名只在验收 readback 时解析实际 Block IDs，不进入 production schema/API。

## 建议的两个 information worlds

### 1. 多地区服务配置与运行证据

一个 mixed information set 同时包含：旧/新官方区域限制、只增加细节的运行说明、不同地区的相似限制、独立测量结果、
复制转述、隐含“该服务”指称和把多个地区放在一个 Block 中的粗粒度记录。

这个 world 允许观察：

- 系统是否区分替代、细化和证据立场；
- 是否避免把美国范围的相似更新当成欧洲范围的 predecessor；
- 是否把复制转述误算为独立证据；
- 是否能把局部隐含指称锚定到既有服务；
- 粒度不足时是否谨慎留下另一个 behavior candidate，而不是对整个 Block 断言；
- later use 是否能取得范围内 current/history 与 count-once evidence。

### 2. 多方事故复盘与修复建议

一个 information set 包含官方 incident timeline、不同团队的观察、相互冲突的原因解释、事后独立验证、复制报道、旧修复
建议及新版方案。部分 material source 只能通过检索或图路径从 initial seed 之外发现。

这个 world 允许观察：

- synthesis 是否形成单一来源没有直接给出的可用结果，同时保留 disagreement、uncertainty 和 speaker attribution；
- 新旧修复方案是否只在 scope/authority 足够时形成 supersession，否则保留 refinement/evidence relation；
- source basis 是否完整可追溯；
- observable upstream `edited` 变化后，相关 synthesis 是否被重新考虑并 append 新版本；
- 一个重复运行轮次是否产生大量重复意义或失控 cascade。

这些 worlds 是初始候选。冻结前应逐项检查它们是否自然承载 Product model，而不是为了覆盖清单生硬拼装；必要时宁可减少
案例并记录 residual，也不构造不真实的万能 corpus。

## 黑盒运行

1. 在 disposable fully migrated PostgreSQL 中，通过正常输入路径写入两个 worlds；此时不写任何 Organization output 或
   candidate edge。
2. 配置真实 provider、purpose-built Agent definitions 和 `core.organization.<behavior>` deployment configs。
3. 从 Job/Cron boundary 启动七种自动 Organization behaviors；不直接调用 Resolver methods，不传 focal IDs、pair、set 或
   主题。运行 bound 与调度顺序作为环境事实记录，而不是作为正确答案。
4. 完成一轮后，通过普通 info-base/Resolver/retrieval/Graph Navigation 使用路径提出上述 later-use 请求并保存 readback。
5. 若第一轮产生 cross-model candidate 或 observable upstream revision，再运行同一组 Jobs 一轮，观察 target behavior、
   append-only response 与重复增长；这不是对失败 case 的随机重试。
6. Human 对完整 before/after/use view 作一次整体评审，并记录 success、reasonable abstention、miss、false authority、runtime
   failure 与 uncovered residual。

## Human 评审提示，而非机械 rubric

评审时优先询问：

- 新图区别是否真的能改善某类后续 query/use，而不是只让图更密或更整齐？
- supersession 是否错误抹高了某条信息的默认地位？
- synthesis 是否诚实保留 material sources、分歧、不确定性和说话者，而不是生成流畅但虚假的统一叙事？
- duplicate 判断是否把独立验证错误折叠，或把同一来源传播错误计为多份证据？
- referent path 是否指向了现实中同一个对象，而不只是名称最像的 Block？
- 系统在证据不足时是否倾向 abstain，而不是制造 graph authority？
- 自动 candidate/search 是否发现了初始邻域之外的关键依据，还是实际被 seeds 限死？

这些问题辅助 Human 形成 best-effort disposition，不转成逐项布尔分数。Exact wording、Tool path、relation 总数和 graph
美观度都不是判断依据。

## 证据与 residual

一次运行保留不含 credential/chain-of-thought 的环境与 readback 摘要：commit、corpus digest、Agent definition/model/tool
identity、config keys、Job outcomes、before/after graph 和 use results。Provider 原始响应、临时数据库与生成内容不成为新的
info-base authority。

默认 residual 包括：未抽样的信息形态、其它语言/领域、长期模型漂移、未实现的真实 Extension behavior、外部 Storage pointer
静默变化，以及小 corpus 无法估计的概率可靠性。发现 material false authority 时应修正并重新执行完整 journey；不能只
挑选一次成功 run 当作证据。

## 可选 fixture 文件组织

若实现成本很低，首版采用 repository 现有 corpus 惯例，而不是把长文本硬编码在 test function：

```text
tests/organization/acceptance/
  corpus.py                    # small manifest reader / alias resolution only
  corpus/
    README.md                  # provenance、许可、维护边界
    manifest.json              # worlds、artifacts、ingestion facts
    regional-service/          # one file per source information artifact
    incident-review/           # one file per source information artifact
  test_black_box.py            # environment setup、Jobs、readback only
```

Manifest 不保存被测系统可见的 expected relations 或 focal hints。外部 pinned artifacts 才需要 URL/retrieved-at/digest；Git
中直接维护的 authored fixture 不再重复 hash。Loader 保持 acceptance-local；第二个真实维护 owner 出现前，不移动到
top-level shared corpus、不创建基类或 registry。若实现时这种拆分没有实际回报，可以保持更少文件而不影响 Acceptance。
