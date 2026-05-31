#!/usr/bin/env bash
# One-shot local install: latest Hermes Agent + DeepSeek + desktop shortcuts (Linux/WSL).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=============================================="
echo " Hermes Agent 本机部署 (DeepSeek)"
echo "=============================================="
echo ""

OS="$(uname -s)"
IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then
  IS_WSL=1
fi

case "${OS}" in
  Linux)
    echo "检测到: Linux$([ "${IS_WSL}" -eq 1 ] && echo ' (WSL)' || echo '')"
    ;;
  Darwin)
    echo "检测到: macOS"
    echo "将安装 Hermes + DeepSeek（macOS 无 .desktop 快捷方式，请用终端 hermes 启动）"
    ;;
  *)
    echo "错误: 不支持的操作系统 ${OS}"
    echo "Windows 请先安装 WSL2 (Ubuntu)，在 WSL 内重新运行本脚本。"
    exit 1
    ;;
esac

if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  echo "请先安装 git 和 curl。"
  exit 1
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo ""
  read -rsp "请输入 DEEPSEEK_API_KEY (sk-...，输入不回显): " DEEPSEEK_API_KEY
  echo ""
  if [ -z "${DEEPSEEK_API_KEY}" ]; then
    echo "错误: 必须提供 DEEPSEEK_API_KEY。也可先 export DEEPSEEK_API_KEY='sk-...' 再运行。"
    exit 1
  fi
  export DEEPSEEK_API_KEY
fi

echo ""
echo "==> [1/3] 安装 / 更新 Hermes Agent ..."
bash "${SCRIPT_DIR}/install-hermes-deepseek.sh"

export PATH="${HOME}/.local/bin:${HOME}/.npm-global/bin:${PATH}"

# Ensure login shell can find hermes
if ! grep -q '.local/bin' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"' >> "${HOME}/.bashrc"
fi

echo ""
echo "==> [2/3] 配置 DeepSeek ..."
hermes config set DEEPSEEK_API_KEY "${DEEPSEEK_API_KEY}"
hermes config set web.search_backend ddgs 2>/dev/null || true

if [ "${OS}" = "Linux" ]; then
  echo ""
  echo "==> [3/3] 安装桌面快捷方式 ..."
  bash "${SCRIPT_DIR}/desktop/install-desktop-shortcuts.sh"
else
  echo ""
  echo "==> [3/3] 跳过桌面快捷方式 (非 Linux)"
fi

echo ""
echo "==> 验证 ..."
hermes --version || true
if hermes doctor 2>&1 | grep -q '✓ DeepSeek'; then
  echo "DeepSeek: OK"
else
  echo "WARN: 请运行 hermes doctor 检查 DeepSeek"
fi

echo ""
echo "=============================================="
echo " 本机部署完成"
echo "=============================================="
if [ "${OS}" = "Linux" ]; then
  echo " 桌面: 双击「Hermes Agent」或「Hermes 控制台」"
  echo "       （若在 ~/Desktop 没有，请看 ~/桌面 或应用菜单）"
fi
echo " 终端: source ~/.bashrc && hermes"
echo " 测试: hermes -z \"你好\""
echo ""
