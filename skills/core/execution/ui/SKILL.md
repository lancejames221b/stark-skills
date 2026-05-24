---
name: ui
description: Voice-driven UI control for <WORKSTATION_HOST> (Kali Linux) and Mac — move windows, launch/close apps, tile/maximize, switch focus, volume, screenshots, sleep display.
category: execution
runtimes: [claude]
pii_safe: true
---

# UI Control Skill — <WORKSTATION_HOST> (Kali Linux) + Mac

Use this skill when the user gives a voice command to control their UI on <WORKSTATION_HOST> or Mac. Parse the intent from natural language and execute immediately — no clarifying questions for simple commands.

## Machine Context

- **<WORKSTATION_HOST>** = Kali Linux workstation (local machine, current session)
- **mac** = MacBook Pro at <PRIVATE_IP>, SSH alias `<MAC_HOST>`, user `lj`
- If the user says "on my mac" / "on the mac" / "mac's X" → run via `ssh <MAC_HOST> "..."`
- If no machine specified and command is X11/window-manager related → <WORKSTATION_HOST>
- If no machine specified and command is app-close/display-sleep/open-mac-app → mac

---

## GAMEZ — Display Layout

```
eDP-1   — primary laptop screen  — 2560x1440  — position x=0,    y=720  (with 2x scale: virtual 3840x2160)
HDMI-1-0 — big 4K external screen — 3840x2160  — position x=3840, y=0
```

**"big screen" / "4K" / "external" / "second display"** = HDMI-1-0 (x=3840)
**"small screen" / "laptop screen" / "built-in"** = eDP-1 (x=0)

### Finding Windows (<WORKSTATION_HOST>)

```bash
# Find by class
xdotool search --classname "google-chrome\|chromium" 2>/dev/null | head -1
xdotool search --name "Slack" 2>/dev/null | head -1

# List all windows
xdotool search --name "." | while read id; do
  name=$(xdotool getwindowname $id 2>/dev/null)
  class=$(xprop -id $id WM_CLASS 2>/dev/null | grep -o '"[^"]*"' | head -1)
  echo "$id [$class]: $name"
done | grep -v "^$"
```

### Move Window to Display (<WORKSTATION_HOST>)

```bash
# Move $WID to big 4K screen
xdotool windowmove $WID 3840 0
xdotool windowsize $WID 3840 2160

# Move $WID to laptop screen
xdotool windowmove $WID 0 720
xdotool windowsize $WID 3840 2160
```

### Window Tiling (<WORKSTATION_HOST>)

```bash
xdotool key super+Left     # tile left half
xdotool key super+Right    # tile right half
xdotool key super+Up       # maximize
xdotool key super+Down     # tile bottom half

# Focus first, then tile
xdotool windowfocus --sync $WID && xdotool key super+Left
```

### Focus / Raise (<WORKSTATION_HOST>)

```bash
wmctrl -ia $WID            # focus + raise + unminimize
xdotool windowfocus --sync $WID && xdotool windowraise $WID
```

### Launch Apps (<WORKSTATION_HOST>)

```bash
setsid google-chrome </dev/null >/dev/null 2>&1 &
setsid /snap/bin/slack </dev/null >/dev/null 2>&1 &
setsid signal-desktop </dev/null >/dev/null 2>&1 &
setsid /opt/Synergy/synergy </dev/null >/dev/null 2>&1 &
setsid 1password </dev/null >/dev/null 2>&1 &
setsid qterminal </dev/null >/dev/null 2>&1 &
setsid thunar </dev/null >/dev/null 2>&1 &
```

### Volume (<WORKSTATION_HOST>)

```bash
pactl set-sink-volume @DEFAULT_SINK@ +10%
pactl set-sink-volume @DEFAULT_SINK@ -10%
pactl set-sink-mute @DEFAULT_SINK@ toggle
```

### Screenshots (<WORKSTATION_HOST>)

```bash
/usr/share/kali-themes/xfce4-screenshooter --fullscreen --clipboard
/usr/share/kali-themes/xfce4-screenshooter --region
/usr/share/kali-themes/xfce4-screenshooter --window
```

### Display Scaling (<WORKSTATION_HOST>)

```bash
# Change xrandr scale (50% = scale 2x2, 25% = scale 4x4, 100% = scale 1x1)
xrandr --output eDP-1 --scale 2x2    # 50%
xrandr --output eDP-1 --scale 1x1    # 100% (reset)

# Font/DPI size (144 = current sweet spot at 50% scale)
xfconf-query -c xsettings -p /Xft/DPI -s 144
```

---

## MAC — Remote Control via SSH

All Mac commands run via `ssh <MAC_HOST> "..."`.

### Close Apps (Mac)

```bash
ssh <MAC_HOST> "osascript -e 'tell application \"Google Chrome\" to quit'"
ssh <MAC_HOST> "osascript -e 'tell application \"Slack\" to quit'"
ssh <MAC_HOST> "osascript -e 'tell application \"Cursor\" to quit'"
ssh <MAC_HOST> "osascript -e 'tell application \"Safari\" to quit'"
ssh <MAC_HOST> "osascript -e 'tell application \"X\" to quit'"  # any app by name
```

### Open / Launch Apps (Mac)

```bash
ssh <MAC_HOST> "open -a 'Google Chrome'"
ssh <MAC_HOST> "open -a 'Slack'"
ssh <MAC_HOST> "open -a 'Cursor'"
ssh <MAC_HOST> "open -a '1Password'"
ssh <MAC_HOST> "open '/path/to/file'"         # open file in default app
ssh <MAC_HOST> "open 'https://example.com'"   # open URL in browser
```

### Display Sleep / Wake (Mac)

```bash
ssh <MAC_HOST> "pmset displaysleepnow"        # sleep display immediately
ssh <MAC_HOST> "caffeinate -u -t 1"           # wake display
```

### Volume (Mac)

```bash
ssh <MAC_HOST> "osascript -e 'set volume output volume 50'"     # set to 50%
ssh <MAC_HOST> "osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'"  # up 10%
ssh <MAC_HOST> "osascript -e 'set volume with output muted'"    # mute
ssh <MAC_HOST> "osascript -e 'set volume without output muted'" # unmute
```

### Screenshots (Mac)

```bash
ssh <MAC_HOST> "screencapture -x ~/Desktop/screenshot.png"      # full screen, no sound
ssh <MAC_HOST> "screencapture -i ~/Desktop/screenshot.png"      # interactive region select
```

### System (Mac)

```bash
ssh <MAC_HOST> "pmset sleepnow"               # sleep the whole Mac
ssh <MAC_HOST> "osascript -e 'tell application \"System Events\" to restart'"
ssh <MAC_HOST> "osascript -e 'tell application \"System Events\" to shut down'"
```

### Ollama (Mac)

```bash
ssh <MAC_HOST> "ollama list"                  # list installed models
ssh <MAC_HOST> "ollama ps"                    # show running models
ssh <MAC_HOST> "ollama run <model>"           # run a model
# Kill all Ollama models from VRAM
ssh <MAC_HOST> "kill \$(pgrep ollama_llama_server) 2>/dev/null"
```

---

## Intent Mapping

| Voice command | Machine | Action |
|---------------|---------|--------|
| "open chrome on <MAC_HOST>" | <MAC_HOST> | `ssh <MAC_HOST> "open -a 'Google Chrome'"` |
| "close chrome on <MAC_HOST>" | <MAC_HOST> | `ssh <MAC_HOST> osascript quit Chrome` |
| "sleep mac display" / "turn off mac screen" | <MAC_HOST> | `ssh <MAC_HOST> pmset displaysleepnow` |
| "wake mac" | <MAC_HOST> | `ssh <MAC_HOST> caffeinate -u -t 1` |
| "mute mac" | <MAC_HOST> | osascript mute |
| "open chrome" / "move chrome to big screen" | <WORKSTATION_HOST> | xdotool launch + move |
| "put slack on big screen" | <WORKSTATION_HOST> | find WID → move to x=3840 |
| "tile X left" | <WORKSTATION_HOST> | focus → super+Left |
| "maximize X" | <WORKSTATION_HOST> | focus → super+Up |
| "close X on <MAC_HOST>" | <MAC_HOST> | osascript quit |
| "volume up on <MAC_HOST>" | <MAC_HOST> | osascript volume |
| "display 50%" | <WORKSTATION_HOST> | xrandr scale 2x2 + DPI 144 |
| "display 100%" | <WORKSTATION_HOST> | xrandr scale 1x1 + DPI 96 |
| "screenshot" | <WORKSTATION_HOST> | xfce4-screenshooter |
| "screenshot on <MAC_HOST>" | <MAC_HOST> | screencapture |

## App Name → Command Mapping

| User says | <WORKSTATION_HOST> launch | mac app name |
|-----------|-------------|--------------|
| chrome / browser | `google-chrome` | `Google Chrome` |
| slack | `/snap/bin/slack` | `Slack` |
| signal | `signal-desktop` | `Signal` |
| 1password | `1password` | `1Password` |
| cursor | — | `Cursor` |
| terminal | `qterminal` | `Terminal` |
| files | `thunar` | `Finder` |
| synergy | `/opt/Synergy/synergy` | `Synergy` |

## Notes

- gamez = local, run commands directly; mac = always `ssh <MAC_HOST> "..."`
- Never kill qterminal — user has active sessions
- For <WORKSTATION_HOST> "bring to front" use `wmctrl -ia` — it also unminimizes
- Current <WORKSTATION_HOST> display scaling: eDP-1 at 2x scale, DPI 144 (sweet spot)
- HDMI-1-0 is at x=3840 (shifted right due to eDP-1 scaling)
- When intent is ambiguous, pick the most likely action and do it
- Confirm what you did in one short sentence after acting
