#!/usr/bin/env bash
# Install Hermes Agent desktop shortcuts (Linux + XFCE/GNOME).
set -euo pipefail
HOME_DIR="${HOME}"
BIN="${HOME_DIR}/.local/bin"
APPS="${HOME_DIR}/.local/share/applications"
ICONS="${HOME_DIR}/.local/share/icons"

# Resolve real desktop folder(s): Desktop, 桌面, XDG user-dirs
DESKTOP_DIRS=()
if [ -f "${HOME_DIR}/.config/user-dirs.dirs" ]; then
  # shellcheck disable=SC1091
  . "${HOME_DIR}/.config/user-dirs.dirs"
  _xdg="${XDG_DESKTOP_DIR:-\$HOME/Desktop}"
  _xdg="${_xdg//\$HOME/${HOME_DIR}}"
  DESKTOP_DIRS+=("$_xdg")
fi
DESKTOP_DIRS+=("${HOME_DIR}/Desktop" "${HOME_DIR}/桌面")
# Deduplicate existing dirs
DESKTOP_UNIQUE=()
for d in "${DESKTOP_DIRS[@]}"; do
  [ -d "$d" ] || mkdir -p "$d" 2>/dev/null || continue
  seen=0
  for u in "${DESKTOP_UNIQUE[@]:-}"; do
    [ "$u" = "$d" ] && seen=1 && break
  done
  [ "$seen" -eq 0 ] && DESKTOP_UNIQUE+=("$d")
done
DESKTOP="${DESKTOP_UNIQUE[0]:-${HOME_DIR}/Desktop}"

mkdir -p "$BIN" "$APPS" "$DESKTOP" "$ICONS"

HERMES_REPO="${HERMES_HOME:-$HOME_DIR/.hermes}/hermes-agent"
if [ -f "${HERMES_REPO}/website/static/img/logo.png" ]; then
  cp "${HERMES_REPO}/website/static/img/logo.png" "${ICONS}/hermes-agent.png"
fi

HERMES_NATIVE="${HERMES_REPO}/apps/desktop/release/linux-unpacked/Hermes"
if [ ! -x "${HERMES_NATIVE}" ]; then
  HERMES_NATIVE="${HERMES_REPO}/apps/desktop/release/linux-unpacked/hermes"
fi

cat > "${BIN}/hermes-desktop-native.sh" << EOF
#!/usr/bin/env bash
export PATH="\${HOME}/.local/bin:\${HOME}/.npm-global/bin:\${PATH}"
export DISPLAY="\${DISPLAY:-:0}"
cd "\${HOME}"
NATIVE="${HERMES_NATIVE}"
if [ -x "\${NATIVE}" ]; then
  exec "\${NATIVE}" "\$@"
fi
exec hermes desktop --skip-build "\$@"
EOF
chmod +x "${BIN}/hermes-desktop-native.sh"

cat > "${BIN}/hermes-desktop-chat.sh" << EOF
#!/usr/bin/env bash
export PATH="\${HOME}/.local/bin:\${HOME}/.npm-global/bin:\${PATH}"
cd "\${HOME}"
if [ -x "${BIN}/hermes-desktop-native.sh" ]; then
  exec "${BIN}/hermes-desktop-native.sh" "\$@"
fi
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
if command -v xfce4-terminal >/dev/null 2>&1; then
  TERM_CMD="xfce4-terminal"
elif command -v gnome-terminal >/dev/null 2>&1; then
  TERM_CMD="gnome-terminal"
elif command -v konsole >/dev/null 2>&1; then
  TERM_CMD="konsole"
else
  TERM_CMD="xterm"
fi

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

case "${TERM_CMD}" in
  xfce4-terminal)
    CHAT_EXEC="${TERM_CMD} --hold -T Hermes Agent -e ${BIN}/hermes-desktop-chat.sh"
    ;;
  gnome-terminal)
    CHAT_EXEC="${TERM_CMD} --title=\"Hermes Agent\" -- ${BIN}/hermes-desktop-chat.sh"
    ;;
  konsole)
    CHAT_EXEC="${TERM_CMD} --hold -p tab -e ${BIN}/hermes-desktop-chat.sh"
    ;;
  *)
    CHAT_EXEC="${TERM_CMD} -hold -e ${BIN}/hermes-desktop-chat.sh"
    ;;
esac

if [ -x "${HERMES_NATIVE}" ] || [ -x "${BIN}/hermes-desktop-native.sh" ]; then
  write_desktop "${APPS}/hermes-agent.desktop" "Hermes Agent" \
    "DeepSeek AI 助手（原生桌面）" \
    "${BIN}/hermes-desktop-native.sh"
else
  write_desktop "${APPS}/hermes-agent.desktop" "Hermes Agent" \
    "DeepSeek AI 助手" \
    "${CHAT_EXEC}"
fi

write_desktop "${APPS}/hermes-dashboard.desktop" "Hermes 控制台" \
  "Web 管理面板" \
  "${BIN}/hermes-desktop-dashboard.sh"

for DESKTOP in "${DESKTOP_UNIQUE[@]}"; do
  cp "${APPS}/hermes-agent.desktop" "${DESKTOP}/Hermes Agent.desktop"
  cp "${APPS}/hermes-dashboard.desktop" "${DESKTOP}/Hermes 控制台.desktop"
  ln -sf "${DESKTOP}/Hermes Agent.desktop" "${DESKTOP}/Hermes智能助手.desktop" 2>/dev/null || true
  chmod +x "${DESKTOP}/Hermes Agent.desktop" "${DESKTOP}/Hermes 控制台.desktop" 2>/dev/null || true
done

update-desktop-database "${APPS}" 2>/dev/null || true

# XFCE: 默认常关闭桌面图标，需显式开启才会显示 ~/Desktop 里的 .desktop
if command -v xfconf-query >/dev/null 2>&1; then
  _style="$(xfconf-query -c xfce4-desktop -p /desktop-icons/style 2>/dev/null || echo 0)"
  if [ "${_style}" = "0" ]; then
    xfconf-query -c xfce4-desktop -p /desktop-icons/style -n -t int -s 2 2>/dev/null \
      || xfconf-query -c xfce4-desktop -p /desktop-icons/style -t int -s 2 2>/dev/null || true
    echo "已开启 XFCE 桌面图标显示"
  fi
  export DISPLAY="${DISPLAY:-:0}"
  xfdesktop --reload 2>/dev/null || true
fi

echo "桌面快捷方式已安装到:"
printf '  - %s\n' "${DESKTOP_UNIQUE[@]}"
