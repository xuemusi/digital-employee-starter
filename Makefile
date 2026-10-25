PYTHON ?= python3
.DEFAULT_GOAL := help

# 用原始 make 变量经环境传参，绝不把学员输入拼接到 shell 命令。
EMPLOYEE_PYTHON := $(value PYTHON)
EMPLOYEE_CATEGORY := $(value CATEGORY)
EMPLOYEE_NAME := $(value NAME)
EMPLOYEE_DESCRIPTION := $(value DESCRIPTION)
unexport PYTHON CATEGORY NAME DESCRIPTION
export EMPLOYEE_PYTHON EMPLOYEE_CATEGORY EMPLOYEE_NAME EMPLOYEE_DESCRIPTION
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: help new check list sync test

help:
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py --help
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py new --help

new:
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py new

check:
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py check

list:
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py list

sync:
	@"$$EMPLOYEE_PYTHON" scripts/employee_tools.py sync

test:
	@"$$EMPLOYEE_PYTHON" -m unittest discover tests -v
