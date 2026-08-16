.PHONY: install init config research batch clean help

# ─── 环境变量（优先从 .env 读取）───
include .env 2>/dev/null || true

# ─── Python 路径 ──
PYTHON  ?= python3
VENV    ?= .venv
PIP     = $(VENV)/bin/pip
RECONBOT = $(VENV)/bin/reconbot

help:
	@echo "===================================="
	@echo "  ReconBot — 常用命令"
	@echo "===================================="
	@echo "  make install    安装依赖"
	@echo "  make init       初始化配置（复制示例）"
	@echo "  make config     查看当前配置"
	@echo "  make research   调研单家公司（需设 COMPANY / WEBSITE）"
	@echo "  make batch      批量调研（需设 CSV_FILE）"
	@echo "  make clean      删除虚拟环境"
	@echo "===================================="

install:
	@echo "[1/3] 创建虚拟环境..."
	$(PYTHON) -m venv $(VENV)
	@echo "[2/3] 升级 pip..."
	$(VENV)/bin/pip install --upgrade pip
	@echo "[3/3] 安装依赖..."
	$(PIP) install -r requirements.txt
	@echo "[可选] 安装可编辑包（获取 reconbot 命令）:"
	$(PIP) install -e .
	@echo ""
	@echo "安装完成。激活: source $(VENV)/bin/activate"
	@echo "或使用: $(VENV)/bin/python -m reconbot.cli"

init:
	@echo "初始化配置文件..."
	@if [ -f config/settings.yaml ] && [ -f config/company_profile.yaml ]; then \
		echo "配置文件已存在，跳过。"; \
	else \
		mkdir -p config; \
		echo "配置文件已就绪 (config/settings.yaml, config/company_profile.yaml)"; \
	fi
	@echo "请编辑 config/settings.yaml 填入 API Key"

config:
	$(VENV)/bin/python -m reconbot.cli config

research:
	@if [ -z "$(COMPANY)" ]; then echo "错误: 未设置 COMPANY"; exit 1; fi
	$(VENV)/bin/python -m reconbot.cli research $(COMPANY) \
		$(shell [ -n "$(WEBSITE)" ] && echo "--website $(WEBSITE)") \
		$(shell [ -n "$(COUNTRY)" ] && echo "--country $(COUNTRY)") \
		$(shell [ -n "$(CITY)" ] && echo "--city $(CITY)") \
		$(shell [ -n "$(PHONE)" ] && echo "--phone $(PHONE)") \
		$(shell [ -n "$(EMAIL)" ] && echo "--email $(EMAIL)")

batch:
	@if [ -z "$(CSV_FILE)" ]; then echo "错误: 未设置 CSV_FILE"; exit 1; fi
	$(VENV)/bin/python -m reconbot.cli batch $(CSV_FILE)

clean:
	rm -rf $(VENV) __pycache__ src/reconbot/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "已清理"
