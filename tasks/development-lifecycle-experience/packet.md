# 开发环境关闭、发布摘要与任务状态维护

目标：落实 Sir 选择的 1、3、4。先整理主工作区，再接通开发环境 stop、补齐生产发布结果摘要、明确 packet 首页维护规则。

边界：python-backend-code 留在本地原位并忽略；Organization 历史记录保留并进入 main。不增加数据库运行时回归矩阵，不改变发布选择、部署命令、权限或生产行为；不清理其他任务环境。新工作从 main `00e30ea` 的 `feat/development-lifecycle-experience` 开始。

当前状态：工作区整理 PR #107 已合并。三项实现和本地验证已完成，准备创建改进 PR。stop 复用现有基于 runtime descriptor 的清理命令；摘要复用已有 append_summary，覆盖空操作、成功和未完成结果；任务规则进入现有 tasks/README.md。

验证结果：完整 pdm run check 通过（14 passed／60 skipped）；actionlint、shell 语法、release intent、diff 检查通过。verify_summary.py 验证空操作、成功、部署／stable 失败、取消和选择失败不误报完成。隔离 worktree 的实例 11223ed63d73adcd 经真实 SSH Docker 创建后，svc dev stop 返回 stopped；容器、卷、descriptor、SSH socket 均已清除，临时 worktree 已删除。主工作区数据库未动。

验证发现并修复边界检查误扫旧扩展 build/ 的问题：改用既有 Ruff 源码清单，验证生成产物被排除且未跟踪的新源码仍受检查。未增加数据库规则。

环境残余：SVC 14 的 ensure 此次 native provision 返回成功，但外层 child-exit 状态携带启动前的缺文件探测；不能作为就绪成功证据。stop 的实际行为通过独立资源读回验证，不在此任务扩展修复外部 SVC。

下一步：提交独立 PR，并核对其远端检查结果。尚无本轮改进 PR 的合并授权。
