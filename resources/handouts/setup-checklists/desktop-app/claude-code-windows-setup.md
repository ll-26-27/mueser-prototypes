# Getting Claude Code working in the desktop app on Windows

When you start a **local Claude Code session** from the Claude desktop app on Windows, two things commonly trip people up. The first hits **almost everyone**: Claude Code needs Git for Windows (and to be told where its `bash.exe` lives). The second is rarer and only matters on some machines: **CPU virtualization** has to be enabled in the BIOS.

Work through Section 1 first. Only go to Section 2 if local sessions still won't start after Git is set up.

---

## 1. Set up Git for Windows (everyone needs this)

Claude Code runs its local sessions through `bash.exe`, which ships with Git for Windows. If Git isn't installed — or Claude Code can't find its `bash.exe` — local sessions won't start.

### Step 1 — Install Git for Windows

Download and run the installer from [git-scm.com](https://git-scm.com). It will request administrator access — accept the prompt. The default options are fine.

### Step 2 — Verify `bash.exe` is present

Open **PowerShell** and run:

```powershell
Test-Path "C:\Program Files\Git\bin\bash.exe"
```

This should return `True`. If it returns `False`, find where Git installed and adjust the path — you want the one ending in `\bin\bash.exe`, **not** `\cmd\git.exe`.

### Step 3 — Set the `CLAUDE_CODE_GIT_BASH_PATH` environment variable

This tells Claude Code exactly where to find `bash.exe`. Run this in PowerShell — no admin needed, it applies to your account:

```powershell
[Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "C:\Program Files\Git\bin\bash.exe", "User")
```

> If you want it set system-wide for all users on the machine, use `"Machine"` instead of `"User"` — but run that from an **admin** PowerShell window.

### Step 4 — (Optional) Add Git to your PATH

If `where.exe git` doesn't find Git, add its `cmd` folder so `git` works from any terminal:

```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\Program Files\Git\cmd", "User")
```

### Step 5 — Confirm everything in a fresh PowerShell window

Open a **new** PowerShell window (environment variables only take effect in windows opened after they're set), then run:

```powershell
[Environment]::GetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "User")
where.exe git
```

The first command should return the `bash.exe` path; the second should return `C:\Program Files\Git\cmd\git.exe`.

### Step 6 — Fully quit and restart the desktop app

Quit the Claude app **completely** (not just closing the window — use the system tray / right-click → Quit) so it picks up the new environment variable on relaunch. Local sessions should now work.

---

## 2. Enable CPU virtualization in BIOS (only if local sessions still won't start)

Some machines ship with CPU virtualization turned off in the BIOS, which can stop local sessions from running. This is **less common** than the Git issue — only come here if Section 1 is done and sessions still fail. The steps below are for a **Lenovo ThinkPad**; other manufacturers are similar but the menu names differ.

### Step 1 — Enter BIOS setup

1. Restart your ThinkPad.
2. As soon as it starts, repeatedly press **F1** (some models use **F2** or **Delete**).
3. You should land on the ThinkPad BIOS/UEFI setup screen.

### Step 2 — Navigate to Security or Advanced settings

Use the arrow keys to go to the **Security** tab (older models) or the **Advanced** tab, then look for a submenu called **Virtualization** or **CPU Settings**.

### Step 3 — Enable virtualization

Enable both of these if available:

- **Intel Virtualization Technology (Intel VT-x)** → set to **Enabled**
- **Intel VT-d Feature** (I/O virtualization) → set to **Enabled**

> On an **AMD** processor, look for **AMD-V** or **SVM Mode** instead.

### Step 4 — Save and exit

Press **F10** to save and exit (or go to the **Exit** tab and choose **Save & Exit**). Confirm when prompted — your PC will restart.

### Step 5 — Verify virtualization is enabled in Windows

After booting into Windows, open **Task Manager → Performance tab → CPU** and confirm that **Virtualization: Enabled** appears.

### Tips if you're having trouble

- Make sure **Secure Boot** isn't blocking the setting — you may need to disable it temporarily.
- On newer ThinkPads the BIOS UI looks different — check under **Security → Virtualization**.
- If the option is **grayed out**, the BIOS may need an update, or the setting is managed by an IT admin (common on corporate/Harvard-managed devices). In that case, contact your local IT support.
