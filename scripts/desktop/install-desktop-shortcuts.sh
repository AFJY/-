#!/usr/bin/env bash
# Install Hermes Agent desktop shortcuts (Linux + XFCE/GNOME).
set -euo pipefail
HOME_DIR="${HOME}"
BIN="${HOME_DIR}/.local/bin"
APPS="${HOME_DIR}/.local/share/applications"
DESKTOP="${HOME_DIR}/Desktop"
ICONS="${HOME_DIR}/.local/share/icons"

mkdir -p "$BIN" "$APPS" "$DESKTOP" "$ICONS"

HERMES_REPO="${HERMES_HOME:-$HOME_DIR/.hermes}/hermes-agent"
if [ -f "${HERMES_REPO}/website/static/img/logo.png" ]; then
  cp "${HERMES_REPO}/website/static/img/logo.png" "${ICONS}/hermes-agent.png"
fi

cat > "${BIN}/hermes-desktop-chat.sh" << 'EOF'
#!/usr/bin/env bash
export PATH="${HOME}/.local/bin:${HOME}/.npm-global/bin:${PATH}"
cd "${HOME}"
exec hermes --tui
EOF

cat > "${BIN}/hermes-desktop-dashboard.sh" << 'EOF'
#!/usr/bin/env bash
export PATH="${HOME}/.local/bin:${HOME}/.npm-global/bin:${PATH}"
PORT="${HERMES_DASHBOARD_PORT:-9119}"
URL="http://127.0.0.1:${PORT}/"
hermes dashboard --stop 2>/dev/null || true
nohup hermes dashboard --port "${PORT}" --no-open --tui >/tmp/hermes-dashboard.log 2>&1 &
sleep 2
xdg-open "${URL}" 2>/dev/null || true
EOF

chmod +x "${BIN}/hermes-desktop-chat.sh" "${BIN}/hermes-desktop-dashboard.sh"

ICON="${ICONS}/hermes-agent.png"
[ -f "$ICON" ] || ICON="utilities-terminal"
TERM_CMD="xfce4-terminal"
command -v xfce4-terminal >/dev/null || TERM_CMD="xterm"

write_desktop() {
  local dest="$1" name="$2" comment="$3" exec_line="$4"
  cat > "$dest" << DESK
[Desktop Entry]
Version=1.0
Type=Application
Name=${name}
Comment=${comment}
Exec=${exec_line}
Icon=${ICON}
Terminal=false
Categories=Development;Utility;
StartupNotify=true
DESK
  chmod +x "$dest"
  gio set "$dest" metadata::trusted true 2>/dev/null || true
}

write_desktop "${APPS}/hermes-agent.desktop" "Hermes Agent" \
  "DeepSeek AI 助手" \
  "${TERM_CMD} --hold -T Hermes Agent -e ${BIN}/hermes-desktop-chat.sh"

write_desktop "${APPS}/hermes-dashboard.desktop" "Hermes 控制台" \
  "Web 管理面板" \
  "${BIN}/hermes-desktop-dashboard.sh"

cp "${APPS}/hermes-agent.desktop" "${DESKTOP}/Hermes Agent.desktop"
cp "${APPS}/hermes-dashboard.desktop" "${DESKTOP}/Hermes 控制台.desktop"
ln -sf "${DESKTOP}/Hermes Agent.desktop" "${DESKTOP}/Hermes智能助手.desktop" 2>/dev/null || true

update-desktop-database "${APPS}" 2>/dev/null || true
echo "桌面快捷方式已安装到 ${DESKTOP}"
