#!/usr/bin/env bash
# =============================================================================
# Hermes Agent + DeepSeek 一键安装（Linux / WSL / macOS）
# 用法:
#   curl -fsSL "https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/oneclick/install-hermes-desktop.sh" | bash
# 或本地:
#   bash scripts/oneclick/install-hermes-desktop.sh
# =============================================================================
set -euo pipefail

REPO_URL="${HERMES_DEPLOY_REPO:-https://github.com/AFJY/-.git}"
REPO_BRANCH="${HERMES_DEPLOY_BRANCH:-cursor/hermes-desktop-deploy-a460}"
INSTALL_DIR="${HERMES_DEPLOY_DIR:-$HOME/hermes-deploy}"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Hermes Agent + DeepSeek  一键安装（本机 + 桌面）      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

OS="$(uname -s)"
case "${OS}" in
  Linux|Darwin) ;;
  *)
    echo "错误: 当前系统 ${OS}。Windows 请使用 Install-HermesDesktop.bat"
    exit 1
    ;;
esac

if ! command -v git >/dev/null || ! command -v curl >/dev/null; then
  echo "请先安装: git curl"
  exit 1
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  read -rsp "DeepSeek API Key (sk-...): " DEEPSEEK_API_KEY
  echo ""
  [ -n "${DEEPSEEK_API_KEY}" ] || { echo "需要 DEEPSEEK_API_KEY"; exit 1; }
  export DEEPSEEK_API_KEY
fi

echo "==> 获取安装脚本 (${REPO_BRANCH}) ..."
if [ -d "${INSTALL_DIR}/.git" ]; then
  git -C "${INSTALL_DIR}" fetch origin
  git -C "${INSTALL_DIR}" checkout "${REPO_BRANCH}" 2>/dev/null || git -C "${INSTALL_DIR}" pull --ff-only || true
else
  git clone --depth 1 --branch "${REPO_BRANCH}" "${REPO_URL}" "${INSTALL_DIR}" 2>/dev/null \
    || { git clone "${REPO_URL}" "${INSTALL_DIR}" && git -C "${INSTALL_DIR}" checkout "${REPO_BRANCH}"; }
fi

export PATH="${HOME}/.local/bin:${PATH}"
bash "${INSTALL_DIR}/scripts/install-local.sh"

echo ""
echo "安装目录: ${INSTALL_DIR}"
echo "配置目录: ~/.hermes"
echo "启动:     source ~/.bashrc && hermes"
echo ""
