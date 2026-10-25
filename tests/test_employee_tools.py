import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "employee_tools.py"


class EmployeeToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve() / "starter root"
        self.root.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(Path(self.temp_dir.name) / "isolated-home")
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, root=None):
        command = [sys.executable, str(SCRIPT)]
        if root is not None:
            command.extend(["--root", str(root)])
        command.extend(args)
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=self.env,
            text=True,
            capture_output=True,
        )

    def write_agent(self, category="general", name="sample", *, description="测试员工", tools="Read, Glob, Grep", model=None, body="\n# 岗位\n\n完整正文。\n"):
        directory = self.root / "agents" / category
        directory.mkdir(parents=True, exist_ok=True)
        fields = {"name": name, "description": description, "tools": tools}
        if model is not None:
            fields["model"] = model
        frontmatter = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False).rstrip()
        (directory / f"{name}.md").write_text(
            f"---\n{frontmatter}\n---{body}", encoding="utf-8"
        )

    def test_new_creates_complete_employee_and_preserves_special_description(self):
        description = '负责整理“已确认需求”：输出可交付文稿。\n不猜测事实。'
        result = self.run_cli(
            "new",
            "--category",
            "general",
            "--name",
            "my-assistant",
            "--description",
            description,
            root=self.root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.root / "agents" / "general" / "my-assistant.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("## 职责", text)
        self.assertIn("## 输入", text)
        self.assertIn("## 输出", text)
        self.assertIn("## 停止条件", text)
        self.assertNotIn("TODO", text)
        document = text.split("---\n", 2)[1]
        metadata = yaml.safe_load(document)
        self.assertEqual(metadata["description"], description)
        self.assertEqual(metadata["tools"], "Read, Glob, Grep")
        self.assertEqual(self.run_cli("check", root=self.root).returncode, 0)

    def test_unresolved_absolute_temp_root_allows_symlink_ancestors(self):
        unresolved_root = Path(self.temp_dir.name) / "unresolved root"
        unresolved_root.mkdir()
        result = self.run_cli(
            "new", "--category", "general", "--name", "unresolved-agent",
            "--description", "临时目录测试员工", root=unresolved_root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_cli("check", root=unresolved_root).returncode, 0)
        self.assertEqual(self.run_cli("sync", root=unresolved_root).returncode, 0)

    def test_make_does_not_expand_shell_functions_in_user_variables(self):
        for variable in ("CATEGORY", "NAME", "DESCRIPTION"):
            with self.subTest(variable=variable):
                copy_root = self.root / variable
                (copy_root / "scripts").mkdir(parents=True)
                shutil.copy2(PROJECT_ROOT / "Makefile", copy_root / "Makefile")
                shutil.copy2(SCRIPT, copy_root / "scripts" / SCRIPT.name)
                values = {"CATEGORY": "general", "NAME": "make-agent", "DESCRIPTION": "中文描述"}
                values[variable] = "$(shell touch make-injected)"
                result = subprocess.run(
                    ["make", "-C", str(copy_root), "new", f"PYTHON={sys.executable}",
                     *(f"{key}={value}" for key, value in values.items())],
                    cwd=PROJECT_ROOT, env=self.env, text=True, capture_output=True,
                )
                self.assertFalse((copy_root / "make-injected").exists(), result.stdout + result.stderr)
                if variable == "DESCRIPTION":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = (copy_root / "agents" / "general" / "make-agent.md").read_text(encoding="utf-8")
                    metadata = yaml.safe_load(text.split("---\n", 2)[1])
                    self.assertEqual(metadata["description"], values[variable])
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse((copy_root / "agents").exists())

    def test_make_preserves_chinese_spaces_quotes_and_shell_characters(self):
        copy_root = self.root / "make copy with spaces"
        (copy_root / "scripts").mkdir(parents=True)
        shutil.copy2(PROJECT_ROOT / "Makefile", copy_root / "Makefile")
        shutil.copy2(SCRIPT, copy_root / "scripts" / SCRIPT.name)
        description = '中文 含空格："双引号"、\'单引号\'； ; touch shell-injected; `touch backtick-injected` $$(touch substitution-injected)'
        result = subprocess.run(
            ["make", "-C", str(copy_root), "new", f"PYTHON={sys.executable}",
             "CATEGORY=general", "NAME=make-agent", f"DESCRIPTION={description}"],
            cwd=PROJECT_ROOT, env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (copy_root / "agents" / "general" / "make-agent.md").read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(text.split("---\n", 2)[1])["description"], description)
        for marker in ("shell-injected", "backtick-injected", "substitution-injected"):
            self.assertFalse((copy_root / marker).exists())
        self.assertFalse(Path(self.env["HOME"]).exists())

    def test_make_treats_python_override_as_executable_path_without_expansion(self):
        for index, payload in enumerate(('python3"; touch python-injected; #', 'python3; touch python-injected', '$(shell touch python-injected)')):
            with self.subTest(payload=payload):
                copy_root = self.root / f"python-case-{index}"
                (copy_root / "scripts").mkdir(parents=True)
                shutil.copy2(PROJECT_ROOT / "Makefile", copy_root / "Makefile")
                shutil.copy2(SCRIPT, copy_root / "scripts" / SCRIPT.name)
                result = subprocess.run(
                    ["make", "-C", str(copy_root), "help", f"PYTHON={payload}"],
                    cwd=PROJECT_ROOT, env=self.env, text=True, capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((copy_root / "python-injected").exists(), result.stdout + result.stderr)

    def test_make_accepts_python_executable_path_with_spaces(self):
        copy_root = self.root / "python path with spaces"
        (copy_root / "scripts").mkdir(parents=True)
        shutil.copy2(PROJECT_ROOT / "Makefile", copy_root / "Makefile")
        shutil.copy2(SCRIPT, copy_root / "scripts" / SCRIPT.name)
        executable = copy_root / "python executable"
        os.symlink(sys.executable, executable)
        result = subprocess.run(
            ["make", "-C", str(copy_root), "help", f"PYTHON={executable}"],
            cwd=PROJECT_ROOT, env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{new,check,list,sync}", result.stdout)

    def test_new_rejects_invalid_names_categories_and_empty_description(self):
        for option, value in (
            ("--category", "General"),
            ("--category", "general/sub"),
            ("--name", "bad_name"),
            ("--name", "-bad"),
            ("--name", "a" * 65),
        ):
            result = self.run_cli(
                "new",
                "--category",
                "general",
                "--name",
                "valid-name",
                "--description",
                "描述",
                option,
                value,
                root=self.root,
            )
            self.assertNotEqual(result.returncode, 0, (option, value, result.stdout, result.stderr))
        result = self.run_cli(
            "new",
            "--category",
            "general",
            "--name",
            "valid-name",
            "--description",
            "   ",
            root=self.root,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_new_rejects_existing_file_and_cross_category_duplicate(self):
        self.write_agent(name="same-name")
        existing = self.root / "agents" / "general" / "new-name.md"
        existing.write_text("existing", encoding="utf-8")
        result = self.run_cli(
            "new",
            "--category",
            "general",
            "--name",
            "new-name",
            "--description",
            "描述",
            root=self.root,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(existing.read_text(encoding="utf-8"), "existing")
        result = self.run_cli(
            "new",
            "--category",
            "other",
            "--name",
            "same-name",
            "--description",
            "描述",
            root=self.root,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "agents" / "other").exists())

    def test_new_rejects_root_symlink_and_does_not_escape_root(self):
        alias = self.root.parent / "root-alias"
        os.symlink(self.root, alias)
        result = self.run_cli(
            "new",
            "--category",
            "general",
            "--name",
            "escape",
            "--description",
            "描述",
            root=alias,
        )
        self.assertNotEqual(result.returncode, 0)
        result = self.run_cli(
            "new",
            "--category",
            "../outside",
            "--name",
            "escape",
            "--description",
            "描述",
            root=self.root,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root.parent / "outside").exists())

    def test_check_rejects_empty_source(self):
        result = self.run_cli("check", root=self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("没有源员工", result.stdout + result.stderr)

    def test_check_rejects_missing_frontmatter_invalid_yaml_duplicate_keys_and_empty_body(self):
        cases = {
            "missing": "# no frontmatter\n正文\n",
            "bad-yaml": "---\nname: bad\ndescription: [\n---\n正文\n",
            "duplicate": "---\nname: duplicate\nname: other\ndescription: 描述\ntools: Read\n---\n正文\n",
            "empty-body": "---\nname: empty-body\ndescription: 描述\ntools: Read\n---\n   \n",
        }
        for name, content in cases.items():
            directory = self.root / "agents" / name
            directory.mkdir(parents=True)
            (directory / f"{name}.md").write_text(content, encoding="utf-8")
            result = self.run_cli("check", root=self.root)
            self.assertNotEqual(result.returncode, 0, name)
            for child in directory.iterdir():
                child.unlink()
            directory.rmdir()

    def test_check_rejects_wrong_fields_values_and_stem(self):
        invalid_documents = [
            ("wrong-name", {"name": "other", "description": "描述", "tools": "Read"}, "正文"),
            ("empty-description", {"name": "empty-description", "description": "", "tools": "Read"}, "正文"),
            ("wrong-tools-type", {"name": "wrong-tools-type", "description": "描述", "tools": 3}, "正文"),
            ("empty-tools", {"name": "empty-tools", "description": "描述", "tools": "Read,,Grep"}, "正文"),
            ("wrong-model", {"name": "wrong-model", "description": "描述", "tools": "Read", "model": ["x"]}, "正文"),
            ("unknown-field", {"name": "unknown-field", "description": "描述", "tools": "Read", "extra": "x"}, "正文"),
        ]
        for filename, fields, body in invalid_documents:
            directory = self.root / "agents" / "general"
            directory.mkdir(parents=True, exist_ok=True)
            frontmatter = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False).rstrip()
            (directory / f"{filename}.md").write_text(
                f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8"
            )
            result = self.run_cli("check", root=self.root)
            self.assertNotEqual(result.returncode, 0, filename)
            (directory / f"{filename}.md").unlink()

    def test_check_accepts_tools_list_and_optional_model(self):
        self.write_agent(name="list-tools", tools=["Read", "Glob"], model="sonnet")
        result = self.run_cli("check", root=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_duplicate_names_across_categories_and_symlink_sources(self):
        self.write_agent(category="first", name="duplicate")
        self.write_agent(category="second", name="duplicate")
        result = self.run_cli("check", root=self.root)
        self.assertNotEqual(result.returncode, 0)
        shutil_path = self.root / "agents" / "second" / "dangling.md"
        os.symlink(self.root / "missing.md", shutil_path)
        result = self.run_cli("check", root=self.root)
        self.assertNotEqual(result.returncode, 0)

    def test_check_rejects_symlink_source_directory(self):
        real = self.root / "real-category"
        real.mkdir()
        (real / "agent.md").write_text("正文", encoding="utf-8")
        (self.root / "agents").mkdir()
        os.symlink(real, self.root / "agents" / "linked-category")
        result = self.run_cli("check", root=self.root)
        self.assertNotEqual(result.returncode, 0)

    def test_list_validates_sources_and_excludes_templates(self):
        self.write_agent(name="listed")
        (self.root / "templates" ).mkdir()
        (self.root / "templates" / "not-an-employee.md").write_text("not valid", encoding="utf-8")
        result = self.run_cli("list", root=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("listed", result.stdout)
        self.assertNotIn("not-an-employee", result.stdout)

    def test_sync_copies_flat_destinations_and_is_idempotent(self):
        self.write_agent(category="general", name="one")
        self.write_agent(category="special", name="two")
        first = self.run_cli("sync", root=self.root)
        self.assertEqual(first.returncode, 0, first.stderr)
        destination = self.root / ".claude" / "agents"
        self.assertEqual(sorted(p.name for p in destination.iterdir()), ["one.md", "two.md"])
        first_bytes = (destination / "one.md").read_bytes()
        second = self.run_cli("sync", root=self.root)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((destination / "one.md").read_bytes(), first_bytes)
        self.assertIn("跳过", second.stdout)

    def test_sync_conflict_is_zero_install_and_does_not_remove_old_destinations(self):
        self.write_agent(name="one")
        self.write_agent(name="two")
        destination = self.root / ".claude" / "agents"
        destination.mkdir(parents=True)
        (destination / "one.md").write_text("local edit", encoding="utf-8")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.run_cli("sync", root=self.root)
        self.assertNotEqual(result.returncode, 0)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((destination / "two.md").exists())
        self.assertIn("备份", result.stdout + result.stderr)

    def test_sync_rejects_destination_symlinks_including_dangling_and_claude_symlink(self):
        self.write_agent(name="one")
        claude = self.root / ".claude"
        real_claude = self.root / "real-claude"
        real_claude.mkdir()
        os.symlink(real_claude, claude)
        result = self.run_cli("sync", root=self.root)
        self.assertNotEqual(result.returncode, 0)
        claude.unlink()
        destination = self.root / ".claude" / "agents"
        destination.mkdir(parents=True)
        os.symlink(self.root / "missing.md", destination / "one.md")
        result = self.run_cli("sync", root=self.root)
        self.assertNotEqual(result.returncode, 0)

    def test_sync_does_not_delete_destination_when_source_removed(self):
        self.write_agent(name="one")
        self.assertEqual(self.run_cli("sync", root=self.root).returncode, 0)
        (self.root / "agents" / "general" / "one.md").unlink()
        result = self.run_cli("sync", root=self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / ".claude" / "agents" / "one.md").exists())

    def test_sync_rejects_source_and_destination_directory_symlinks(self):
        self.write_agent(name="one")
        agents = self.root / "agents"
        real_agents = self.root / "real-agents"
        agents.rename(real_agents)
        os.symlink(real_agents, agents)
        result = self.run_cli("sync", root=self.root)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
