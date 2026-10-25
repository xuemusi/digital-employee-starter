# 第一次拉取后，交给 AI 使用

拉取仓库后即可开始，不必先手动准备 Python 环境或安装岗位。
前提是你已安装且授权可用的 Claude Code；请从本仓根目录打开它，发送：

```text
请读取仓库根目录的 START-HERE.md，按首次使用流程带我完成环境检查、项目内安装和第一次数字员工任务；执行安装前先说明改动并征得我确认。
```

以下是给 AI 主会话的首次使用操作协议，不是已经执行成功的记录。
其他 AI 若没有文件、命令或独立 Agent 工具，只能给出步骤并说明能力限制，不得假称执行。

## 1. 先确认位置与范围

- 确认当前工作目录是本仓根目录，能看到 README.md、CLAUDE.md、Makefile 和 agents/。
- 若位置不符，先请用户在正确根目录打开会话；不要把文件写到别的仓库。
- 先读取 README.md、CLAUDE.md、Makefile、requirements.txt、docs/quickstart.md 和 teams/document-team/TEAM.md。
- 只看本次必需的项目文件，不扫描其他项目、私人目录、全局配置或凭据。
- 本仓不是独立沙箱；遵守实际生效的权限，不修改安全设置，也不自行读取全局配置来“排查”。

## 2. 只做最小环境检查

- 检查 Python 3.10+、make 及本地所需工具是否可用；检查本仓是否已有 .venv/。
- 此时不要求用户先发现尚未安装的岗位，也不调用模型做业务任务。
- 缺少系统工具时，报告缺项和适用平台的最小准备步骤，等待用户处理。
- 不使用 sudo、不全局安装、不自动安装系统工具，不改账号、授权或安全设置。
- 已有 .venv/ 时检查其解释器是否可用、版本是否满足要求；不能确认可用就停下说明。
- 不覆盖、删除或重建已有 .venv/；需要改变方案时重新征求用户确认。

## 3. 说明改动，确认后才安装

先展示计划：在本仓创建或复用可用 .venv/，通过 pip 联网安装 requirements.txt 中的依赖，
运行本地检查与测试，并把三个源岗位复制到本项目 .claude/agents/。
明确当前依赖为 PyYAML>=6,<7，安装会下载依赖并修改本地环境；不写 HOME，不安装全局岗位。
展示将执行的命令和涉及路径，询问用户是否同意；未获明确确认前不安装、不同步。

用户确认后，仅在已核对的本仓根目录执行。没有 .venv/ 时先创建：

```bash
python3 -m venv .venv
```

确认新建或复用的环境可用后，逐条执行并记录真实结果：

```bash
.venv/bin/python -m pip install -r requirements.txt
make check PYTHON=.venv/bin/python
make list PYTHON=.venv/bin/python
make test PYTHON=.venv/bin/python
make sync PYTHON=.venv/bin/python
```

任何命令失败就停下报告，不把未执行项算完成。同步冲突先保留现状并核对，不 force、不删除文件绕过保护。

## 4. 区分安装成功与岗位就绪

- 命令实际成功只证明本地工具与安装步骤完成，不证明岗位已可调度或模型效果合格。
- 安装后核验当前会话是否真实发现 task-planner、document-writer、quality-reviewer，是否具备独立 Agent 调用能力。
- 核对岗位来自本项目 .claude/agents/；只看必需项目定义，不读取全局目录排查同名岗位。
- 找不到岗位或无法确认来源、调用能力时，报告 blocked，不角色扮演、不伪装完成。
- 必要时请用户从本仓根目录新开 Claude Code 会话，提供以下续接句；新会话仍须实际核验，不默认就绪：

```text
请读取 START-HERE.md，先核对现有项目安装和当前会话的三个岗位发现、来源及真实调用能力；不要重复安装。就绪后问我先跑虚构书店示例还是自己的真实任务。
```

## 5. 就绪后由用户选任务

简短介绍三岗：task-planner 梳理需求；document-writer 按确认事实写稿；quality-reviewer 独立检查。
然后问用户先跑“虚构书店示例”还是“自己的真实任务”，不默认开始，也不自动新建业务岗位。

- 选示例：读取 examples/document-task/prompt.md，遵循 teams/document-team/TEAM.md；不覆盖源资料或参考文稿。
- 选真实任务：仅询问完成任务必需的目标、授权材料、读者、限制和输出位置，不扩大资料范围。
- 真实调用 planner → 展示需求并等用户确认 → 主会话检查输出目录及文件冲突 → 调用 writer → 另行调用独立 reviewer → 用户验收。
- reviewer 只拿确认要求、事实、当前正文，不拿 writer 自评；改稿后重新独立检查，不让同一上下文演三人补通过。
- 工具检查与模型任务效果分开报告；实际模型调用消耗学员自己的额度，不承诺免费或正确。
- 云模型读取本地文件时内容仍可能外发，只处理用户明确授权的资料；不执行无关外发、上传、发布或 git commit/push。
- 缺信息、权限、工具或岗位能力就报告 blocked；文件未实际写入不报“已生成”，独立检查不替代用户验收或发布授权。

手动安装仅作备用，见 [快速开始](docs/quickstart.md)；具体协作细则以 [TEAM](teams/document-team/TEAM.md) 为准。
