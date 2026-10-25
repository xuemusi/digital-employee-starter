# 快速开始：完成第一次真实派工

## 先让 AI 带路

拉取仓库后即可从本仓根目录打开已安装且授权可用的 Claude Code，不必先完成下面的手动安装。复制这一句话：

```text
请读取仓库根目录的 START-HERE.md，按首次使用流程带我完成环境检查、项目内安装和第一次数字员工任务；执行安装前先说明改动并征得我确认。
```

仓库自带的 [START-HERE.md](../START-HERE.md) 会指导 AI 先检查环境、说明改动并征得确认，再做项目内安装，最后核验岗位并让你选择任务。没有文件或命令工具的其他 AI 只能给步骤，不能声称已执行。

## 以下为手动安装备用步骤

适用 macOS/Linux；Windows 使用 WSL。手动路径需要 Python 3.10+、make，以及已安装且授权可用的 Claude Code。本教程不安装全局角色，也不提供账户、凭据或第三方连接。

### 1. 进入收到的起步包根目录

在终端打开 `digital-employee-starter/`，确认这里能看到 README.md、Makefile 和 agents/。下列命令均在此目录执行，每条单独运行；不需要写死个人路径。

先审查本机全局配置、插件和权限。本项目不是独立沙箱，不会替你隔离上级或个人配置。

## 2. 创建本地 Python 环境

```bash
python3 -m venv .venv
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

依赖为 `PyYAML>=6,<7`。不必激活环境，也不要改成全局安装；安装依赖需要联网，检查和测试本身不调用模型。

## 3. 检查、列出、同步、测试

```bash
make check PYTHON=.venv/bin/python
```

```bash
make list PYTHON=.venv/bin/python
```

```bash
make sync PYTHON=.venv/bin/python
```

```bash
make test PYTHON=.venv/bin/python
```

检查无误后应能列出三个源岗位：task-planner、document-writer、quality-reviewer。测试只验证工具行为，不代表员工已经实际写稿或完成独立检查。

同步会把源文件复制到本项目 `.claude/agents/`，不写 HOME。内容完全相同可跳过；任何同名文件不同都会先全量冲突失败、本轮零安装，不覆盖或删除其他员工。

若冲突，先核对源文件和本地副本，备份本地需要的修改；再由你手工移开冲突目标或统一两边内容，然后重试。不要直接删除文件绕过冲突保护。

不使用脚本时，可手工在本项目创建 `.claude/agents/`，把 `agents/general/` 的三个 `.md` 文件完整复制进去。模板不复制；有差异的同名文件先停下核对，手工方式没有全量冲突保护。

## 4. 新开根目录会话

第一次安装后，建议从本仓根目录新开 Claude Code 会话，这是较稳妥的发现方式。更新后是否需要重开应以当前版本的发现情况为准，不是一律必须重启。

请主会话核对三个岗位来自本项目，并具有真实 Agent 调用能力。岗位找不到就报告 blocked，先检查安装与当前目录；不要在同一上下文演三个人。

打开仓库根目录的 [第一次使用提示词](../START-HERE.md)，将整段内容复制到新会话。它会先让 AI 检查环境，再按真实的岗位分工处理后续任务。

## 5. 跑一次虚构文稿任务

如果要跑虚构示例，打开 `examples/document-task/prompt.md`，把其中整段提示词复制到这个新会话；如果要处理自己的任务，先使用仓库根目录的 `START-HERE.md`。

本例只处理 `examples/document-task/input.md` 的原创虚构信息；云模型读取本地材料时仍可能外发，不要夹带未授权资料。

正常顺序是：

1. 主会话真实调用 task-planner，拿到需求单。
2. 主会话向你确认，你明确同意后才继续。
3. 主会话先创建并检查 `output/document-task/`，确认可写且不会覆盖既有交付，再真实调用 document-writer 写正文。writer 不负责创建父目录；主会话无创建目录能力时报告 blocked。
4. 主会话另行真实调用 quality-reviewer，只传要求、事实、当前正文，不传作者自评。
5. 有修改就重新独立检查，最后由你验收。

产物放在 `output/document-task/`。源材料与 `reference-output.md` 不覆盖；后者只是格式参考，不是已执行或已审核的证据。文件没写成，就应如实报告未写入。

真实调用会消耗你自己的 Claude Code 额度；本包没有免费后台运行承诺。检查通过、用户验收、对外发布是三件不同的事。

## 6. 再定制一位员工

```bash
make new CATEGORY=general NAME=my-assistant DESCRIPTION='整理授权资料并输出摘要' PYTHON=.venv/bin/python
```

打开生成的 `agents/general/my-assistant.md`，对照 `templates/agent-template.md` 按实际业务修改：目标、输入、输出、验收、阻断条件和最少工具权限。初稿不等于成熟部署。

修改后先检查：

```bash
make check PYTHON=.venv/bin/python
```

再同步：

```bash
make sync PYTHON=.venv/bin/python
```

若旧副本与新源文件不同，按第3节核对与备份后解决冲突，不强制覆盖。先用无敏感信息的小任务验证，再安排独立检查。

## 交给别人之前

按允许清单整理，或另取干净目录；排除 `.venv/`、`.claude/agents/`、`output/`、`private/`、`.env`、凭据和日志。打 zip 不会自动遵循 `.gitignore`，分享前手工检查内容及素材授权。

更多概念、工具边界与官方依据见 [README](../README.md)；具体派工约定见 [文稿战队协议](../teams/document-team/TEAM.md)。
