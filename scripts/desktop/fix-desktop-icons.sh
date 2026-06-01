#!/usr/bin/env bash
# 修复「桌面没有图标」：开启 XFCE 桌面图标 + 重装快捷方式 + 刷新
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DISPLAY="${DISPLAY:-:0}"

echo "==> 重装 Hermes 桌面快捷方式 ..."
bash "${SCRIPT_DIR}/install-desktop-shortcuts.sh"

if command -v xfconf-query >/dev/null 2>&1; then
  echo "==> 开启 XFCE 桌面图标 ..."
  xfconf-query -c xfce4-desktop -p /desktop-icons/style -n -t int -s 2 2>/dev/null \
    || xfconf-query -c xfce4-desktop -p /desktop-icons/style -t int -s 2
  xfdesktop --reload 2>/dev/null || xfdesktop --replace &
fi

echo ""
echo "完成。请查看桌面是否出现："
echo "  - Hermes Agent"
echo "  - Hermes 控制台"
echo ""
echo "若仍没有：右键桌面 → 桌面设置 → 图标 → 类型选「文件/启动器图标」"
