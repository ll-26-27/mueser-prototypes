# Claude Code Setup (Windows)

This guide takes a fresh Windows machine to a working Claude Code environment with the
workshop repo cloned and open in VS Code. Run everything in **PowerShell** (your prompt
should start with `PS`). You do **not** need to run as Administrator.

Estimated time: 15–25 minutes, mostly waiting on downloads.

---

## Before you start

- You need a **paid Claude account** (Pro, Max, Team, or Enterprise). The free plan does
  not include Claude Code.
- `winget` is built into Windows 11 and modern Windows 10. Confirm it works:
  ```powershell
  winget --version
  ```
  If that errors, install "App Installer" from the Microsoft Store, then reopen PowerShell.
  
  An example of an error caused by `winget` not being installed:
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4LMNJ399/image.png?pub_secret=44e5c54983)

If you get the error above, it is also possible that the app is installed but may not be in your **PATH**. Open your powershell and Run this: 

```powershell
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$env:LOCALAPPDATA\Microsoft\WindowsApps", "User")
```

Then **restart PowerShell** and try again:

```powershell
winget --version
```
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B5MJ5EHL0/image.png?pub_secret=3048b491fc)
---

## Step 1 — Install the core tools with winget

Run these four commands one at a time commands. Each downloads and installs silently.



```powershell
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
```

```powershell
winget install --id OpenJS.NodeJS -e --accept-source-agreements --accept-package-agreements
```

```powershell
winget install --id Microsoft.VisualStudioCode -e --accept-source-agreements --accept-package-agreements
```

```powershell
winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements
```


Examples of successful installation in PowerShell:

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4TBQCEAE/image.png?pub_secret=093ae5c1fc)

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4M21H6QK/image.png?pub_secret=3f7f8cdc09)



Notes:
- `-e` forces an exact match on the package ID so you get the right package.
- If winget says a package is **already installed**, that's fine — skip it.
- If it asks you to accept source agreements, type `Y`.
- The Git installer's defaults are correct for this workshop — in particular it adds Git
  to your PATH, which Claude Code needs.

When all four finish, **close PowerShell completely and open a fresh window.** This is
required — installers update your PATH, and an already-open terminal won't see the change.

---

## Step 2 — Verify the core tools

In the new PowerShell window, check the status of your installs by running each of these commands one at a time:

```powershell
git --version
```
```powershell
node --version
```
```powershell
npm --version
```
```powershell
python --version
```
```powershell
code --version
```
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4TE0AEV8/image.png?pub_secret=aec21900bb)

You should get a version number from each (above). Three common snags:

- **`npm --version` errors with "running scripts is disabled on this system":** PowerShell's default execution policy (`Restricted`) blocks all scripts, and `npm` on Windows is actually a PowerShell script (`npm.ps1`) — so PowerShell refuses to run it. You'll see something like this:

  ```
  PS C:\Users\you> npm --version
  npm : File C:\Program Files\nodejs\npm.ps1 cannot be loaded because running
  scripts is disabled on this system. For more information, see
  about_Execution_Policies at https://go.microsoft.com/fwlink/?LinkID=135170.
      + CategoryInfo          : SecurityError: (:) [], PSSecurityException
      + FullyQualifiedErrorId : UnauthorizedAccess
  ```

  Fix it from your normal (non-admin) PowerShell window:

  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

  Type `Y` when prompted. `RemoteSigned` allows locally-installed scripts (like npm's) to run while still requiring scripts downloaded from the internet to be digitally signed — the standard developer setup on Windows. `-Scope CurrentUser` applies the change only to your account, which is why no admin is required. Close and reopen PowerShell, then re-run `npm --version`.

- **`python --version` opens the Microsoft Store or says "Python was not found":** the Windows Store stub is shadowing your real Python install. You'll see something like this:

  ```
  PS C:\Users\you> python --version
  Python was not found; run without arguments to install from the Microsoft
  Store, or disable this shortcut from Settings > Manage App Execution Aliases.
  ```

  Fix it by going to **Settings → Apps → Advanced app settings → App execution aliases** and turning **off** the toggles for `python.exe` and `python3.exe`, then reopening PowerShell.

  ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B5MP73CDN/image.png?pub_secret=c4aa1769f7)
  ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4X3QRZ0C/image.png?pub_secret=ffe285bc2e)

- **`code --version` errors with "not recognized":** VS Code's CLI shim isn't on your PATH yet — usually because the terminal was opened before the installer finished updating PATH. You'll see something like this:

  ```
  PS C:\Users\you> code --version
  code : The term 'code' is not recognized as the name of a cmdlet, function,
  script file, or operable program. Check the spelling of the name, or if a
  path was included, verify that the path is correct and try again.
      + CategoryInfo          : ObjectNotFound: (code:String) [], CommandNotFoundException
      + FullyQualifiedErrorId : CommandNotFoundException
  ```

  Fix: close and reopen PowerShell once more. If it still fails in a fresh window, open VS Code manually, press `Ctrl+Shift+P`, and run **"Shell Command: Install 'code' command in PATH"**, then reopen PowerShell again.


---

## Step 3 — Install the Claude Code CLI

Run the official native installer in PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

This installs the `claude` binary to `C:\Users\<your-username>\.local\bin`. No Node.js is
required for Claude Code itself.

When it finishes, **close PowerShell and open a fresh window**, then check:

```powershell
claude --version
```
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4RES08SJ/image.png?pub_secret=53fca27515)

### If you get "claude is not recognized"

This is a known issue — the installer sometimes doesn't add its folder to your PATH.
Fix it with this command: 

```powershell
$new = "$env:USERPROFILE\.local\bin"
$current = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$current;$new", "User")
```

Then **fully close every PowerShell window**, open a new one, and try `claude --version`
again. Once it works, run a quick health check:

```powershell
claude doctor
```
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4X5K217W/image.png?pub_secret=72fee9eb0f)
---

## Step 4 — Create the workspace folder and clone the repo

In PowerShell, create a folder for your projects:

```powershell
cd $env:USERPROFILE
mkdir Development
cd Development
git clone https://github.com/ll-26-27/eng298ai-20261103.git
```

Adjust the first line if your projects live somewhere else. The repo is public, so cloning needs no login. It clones into a subfolder named `eng298ai-20261103`.

An example of cloning the repo into a local folder:
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4C5KGB47/image.png?pub_secret=4f4ad17e2b)

---

## Step 5 — Open the project in VS Code

```powershell
cd eng298ai-20261103
code .
```
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4TKY615Y/image.png?pub_secret=92f386d600)

VS Code opens with the project loaded. If it asks **"Do you trust the authors of the
files in this folder?"**, choose **Yes, I trust the authors** — otherwise some features
stay disabled.

---

## Step 6 — Log in to Claude in the integrated terminal

1. In VS Code, open the integrated terminal: **Terminal → New Terminal**
   (or `` Ctrl+` ``).
   ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4VGECD9P/image.png?pub_secret=5b31c14413)
2. Confirm you're at the project root — the prompt should end in
   `...\claude-code\eng298ai-20261103`.
   ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4XA6ATL4/image.png?pub_secret=f23f6ddaf1)
3. Start Claude Code:
   ```powershell
   claude
   ```
   ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4C8M2MGF/image.png?pub_secret=bfbe2f2e08)
4. On first run it walks you through login. Choose your account option and a browser
   window opens for sign-in. Log in with your paid Claude account and approve the
   request. The browser will say you can return to the terminal.
5. Back in the terminal, Claude Code is ready. Type a message to confirm it responds,
   e.g. *"What files are in this project?"*
   ![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4MBLRFRR/image.png?pub_secret=c55afd35a0)

To exit Claude Code, type `/exit` or press `Ctrl+C` twice.
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4VJ4LW73/image.png?pub_secret=837030ca1c

Let me check the current state of the Claude Code VS Code extension before drafting — install steps and UI shift around, and I want this to match what your workshop participants will actually see.Here's Step 7 — a drop-in section that slots after Step 6 and before Quick Reference, in the same style as the rest of the handout. I've verified the current install flow against the official docs and a few independent guides, since the extension UI shifted recently.

---

## Step 7 — (Optional) Add the Claude Code side panel in VS Code

If you'd rather work with Claude in a dedicated chat panel inside VS Code — with inline diffs, a sessions list, and @-mention file picking — install the official extension. You still get everything from Step 6; this just adds a graphical interface on top of the same login.

1. In VS Code, open the **Extensions** view: click the puzzle-piece icon in the Activity Bar on the left, or press `Ctrl+Shift+X`.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UFXUW7L/screenrecording2026-05-19at11.40.12am-ezgif.com-video-to-gif-converter.gif?pub_secret=46fbad2613)

2. Search for **Claude Code**. Install the one published by **Anthropic** — there are similarly-named knock-offs, so check the publisher field before clicking Install.

3. After it installs, click the **Spark icon** (✱) that appears in the Activity Bar on the left to open the Claude Code panel. If you don't see the icon, open the Command Palette (`Ctrl+Shift+P`), type **Claude Code**, and pick **"Claude Code: Open in Sidebar"**.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UGPE0LA/screenrecording2026-05-19at11.40.54am-ezgif.com-video-to-gif-converter.gif?pub_secret=3bdbbcbfd0)

4. The first time you open the panel, a sign-in screen appears. Click **Sign in** and complete authorization in the browser window that opens. Log in with your paid Claude account and approve the request — same flow as Step 6.

5. Back in VS Code, try a message in the chat panel, e.g. *"What files are in this project?"* When Claude proposes edits, they render as inline diffs in the panel — click a diff to expand it, then accept or reject from the panel itself.

Notes:

- **Pin the panel so it survives restarts:** open VS Code settings (`Ctrl+,`), search for `claudeCode.preferredLocation`, and set it to **sidebar**. Without this, the panel can disappear when you reload the window.
- **CLI and extension don't always share credentials.** If the panel shows a sign-in screen even after Step 6, that's expected — just sign in once more from the panel.
- **Requires VS Code 1.98 or higher.** If you installed VS Code via winget in Step 1, you're already current.
- **Open files with `@`:** in the panel's prompt box, type `@` to fuzzy-search files in your project. This is faster and more reliable than pasting paths.

---

A couple of small additions you may want to fold into the existing Quick Reference and Troubleshooting blocks so they stay in sync:

**Quick reference** — one new row:

| Open Claude Code panel | Click ✱ in Activity Bar, or `Ctrl+Shift+P` → "Claude Code" |

**Troubleshooting** — two new bullets:

- **Claude Code panel disappears after restarting VS Code** — set `claudeCode.preferredLocation` to `sidebar` in VS Code settings (`Ctrl+,`).
- **Spark icon missing from the Activity Bar** — confirm the extension is published by **Anthropic** (not a similarly-named third-party), and reload the window from the Command Palette: **Developer: Reload Window**.

A note on framing: I positioned this as "(Optional)" because the CLI in Step 6 is genuinely sufficient for the workshop — making the panel optional keeps participants who hit installer trouble from feeling stuck. If you'd rather make it the recommended default (which is what Anthropic's docs do now), just drop the "(Optional)" and adjust the lead sentence to "Most participants will prefer the side panel — here's how to set it up."

---

## Quick reference

| Goal | Command |
|------|---------|
| Check a tool is installed | `git --version`, `node --version`, etc. |
| See where a command lives | `Get-Command claude` (PowerShell's `which`) |
| Claude Code health check | `claude doctor` |
| Update Claude Code | auto-updates in the background |
| Update winget packages | `winget upgrade --all` |
| Start Claude Code | `claude` (from the project folder) |
| Exit Claude Code | `/exit` |

---

## Troubleshooting

- **A command "is not recognized" right after installing it** — almost always a stale
  PATH. Close every terminal window and open a fresh one.
- **`claude` still not found after the PATH fix** — confirm the binary exists with
  `Test-Path "$env:USERPROFILE\.local\bin\claude.exe"`. If `True`, you have a stale
  terminal; if `False`, re-run the Step 3 installer.
- **Browser login gets stuck in a loop** — try a different browser for the initial
  sign-in, or temporarily relax strict tracker/cookie blocking.
- **Claude Code can't find Git Bash** — make sure Step 1's Git install completed; Claude
  Code falls back to PowerShell without it, which works but is less smooth.