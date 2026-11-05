# Claude Code Setup (macOS)

This guide takes a fresh Mac to a working Claude Code environment with the workshop repo cloned and open in VS Code. Run everything in the **Terminal app** (your prompt should end in `%` or `$`). You do **not** need `sudo` for any of these steps.

Estimated time: 15–25 minutes, mostly waiting on downloads.

---

## Before you start

- You need a **paid Claude account** (Pro, Max, Team, or Enterprise). The free plan does not include Claude Code.
- Open the **Terminal app**: press `Cmd+Space`, type **Terminal**, and press Enter.
- You need **Homebrew** (`brew`), the standard package manager for macOS. Confirm it's installed:
  ```bash
  brew --version
  ```
  If that errors with "command not found," install Homebrew by pasting this into Terminal:
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
  The installer takes 5–10 minutes and may prompt for your Mac password (this is normal — it's installing system-level tools).

  When it finishes, the installer prints two commands you need to run to add `brew` to your PATH. On **Apple Silicon Macs (M1/M2/M3/M4)** they look like this:
  ```bash
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
  ```
  On **Intel Macs**, the path is `/usr/local/bin/brew` instead. Copy the exact commands the installer prints — they're customized for your machine.

  Then **close Terminal completely (`Cmd+Q`) and open a fresh window**, and confirm:
  ```bash
  brew --version
  ```
  You should see a version number like `Homebrew 4.x.x`.

---

## Step 1 — Install the core tools with brew

Run these four commands one at a time. Each downloads and installs silently.

```bash
brew install git
```
```bash
brew install node
```
```bash
brew install --cask visual-studio-code
```
```bash
brew install python@3.13
```

Notes:
- `--cask` is required for GUI apps like VS Code; without it, brew won't find the package.
- If brew says a package is **already installed**, that's fine — skip it. If you want the latest version, run `brew upgrade <package>` instead.
- `brew install node` includes `npm` automatically — no separate install needed.
- The Git from Homebrew is newer than the one Apple ships with Xcode Command Line Tools. Claude Code works with either, but the Homebrew one stays up to date via `brew upgrade`.

When all four finish, **close Terminal completely (`Cmd+Q`) and open a fresh window.** This is required — installers update your PATH, and an already-open terminal won't see the change.

---

## Step 2 — Verify the core tools

In the new Terminal window, check the status of your installs by running each of these commands one at a time:

```bash
git --version
```
```bash
node --version
```
```bash
npm --version
```
```bash
python3 --version
```
```bash
code --version
```

You should get a version number from each. Three common snags:

- **`git --version` triggers an Xcode Command Line Tools installer:** on a fresh Mac, the first time anything asks for `git`, macOS may pop up a dialog asking to install the Command Line Tools. You'll see something like this:

  ```
  % git --version
  xcode-select: note: No developer tools were found, requesting install.
  ```

  Click **Install** in the dialog and wait — it takes 5–10 minutes. Once it finishes, re-run `git --version`. (If you already installed Git via Homebrew in Step 1, you may not see this prompt at all — brew's Git takes precedence.)

- **`python --version` says "command not found," but `python3 --version` works:** macOS doesn't include a `python` command by default — only `python3`. This is intentional, since `python` historically meant Python 2 and Apple removed it. You'll see something like this:

  ```
  % python --version
  zsh: command not found: python
  ```

  For this workshop, **use `python3` everywhere instead of `python`** — that's the canonical name on macOS. If you really want `python` to work as an alias, add this to your `~/.zshrc`:

  ```bash
  echo 'alias python=python3' >> ~/.zshrc
  source ~/.zshrc
  ```

  But it's cleaner to just use `python3` and match what macOS expects.

- **`code --version` errors with "command not found":** VS Code's CLI shim isn't on your PATH yet. Unlike Windows, the macOS VS Code installer doesn't add `code` to your PATH automatically — you have to do it from inside VS Code. You'll see something like this:

  ```
  % code --version
  zsh: command not found: code
  ```

  Fix: open VS Code (`Cmd+Space` → "Visual Studio Code"), press `Cmd+Shift+P` to open the Command Palette, type **shell command**, and select **"Shell Command: Install 'code' command in PATH"**. You may be prompted for your Mac password. Then close and reopen Terminal, and `code --version` will work.

---

## Step 3 — Install the Claude Code CLI

Run the official native installer in Terminal:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

This installs the `claude` binary to `~/.local/bin`. No Node.js is required for Claude Code itself.

When it finishes, **close Terminal and open a fresh window**, then check:

```bash
claude --version
```

### If you get "claude: command not found"

The installer sometimes doesn't add its folder to your PATH. Fix it by adding this line to your `~/.zshrc`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Then **fully close every Terminal window (`Cmd+Q`)**, open a new one, and try `claude --version` again. Once it works, run a quick health check:

```bash
claude doctor
```

---

## Step 4 — Create the workspace folder and clone the repo

In Terminal, create a folder for your projects:

```bash
cd ~
mkdir Development
cd Development
git clone https://github.com/ll-26-27/eng298ai-20261103.git
```

Adjust the first line if your projects live somewhere else. The repo is public, so cloning needs no login. It clones into a subfolder named `eng298ai-20261103`.

---

## Step 5 — Open the project in VS Code

```bash
cd eng298ai-20261103
code .
```

VS Code opens with the project loaded. If it asks **"Do you trust the authors of the files in this folder?"**, choose **Yes, I trust the authors** — otherwise some features stay disabled.

---

## Step 6 — Log in to Claude in the integrated terminal

1. In VS Code, open the integrated terminal: **Terminal → New Terminal** (or `` Ctrl+` ``).
2. Confirm you're at the project root — the prompt should end in `...eng298ai-20261103 %`.
3. Start Claude Code:
   ```bash
   claude
   ```
4. On first run it walks you through login. Choose your account option and a browser window opens for sign-in. Log in with your paid Claude account and approve the request. The browser will say you can return to the terminal.
5. Back in the terminal, Claude Code is ready. Type a message to confirm it responds, e.g. *"What files are in this project?"*

To exit Claude Code, type `/exit` or press `Ctrl+C` twice.

---

## Step 7 — (Optional) Add the Claude Code side panel in VS Code

If you'd rather work with Claude in a dedicated chat panel inside VS Code — with inline diffs, a sessions list, and @-mention file picking — install the official extension. You still get everything from Step 6; this just adds a graphical interface on top of the same login.

1. In VS Code, open the **Extensions** view: click the puzzle-piece icon in the Activity Bar on the left, or press `Cmd+Shift+X`.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UFXUW7L/screenrecording2026-05-19at11.40.12am-ezgif.com-video-to-gif-converter.gif?pub_secret=46fbad2613)

2. Search for **Claude Code**. Install the one published by **Anthropic** — there are similarly-named knock-offs, so check the publisher field before clicking Install.
3. After it installs, click the **Spark icon** (✱) that appears in the Activity Bar on the left to open the Claude Code panel. If you don't see the icon, open the Command Palette (`Cmd+Shift+P`), type **Claude Code**, and pick **"Claude Code: Open in Sidebar"**.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UGPE0LA/screenrecording2026-05-19at11.40.54am-ezgif.com-video-to-gif-converter.gif?pub_secret=3bdbbcbfd0)

4. The first time you open the panel, a sign-in screen appears. Click **Sign in** and complete authorization in the browser window that opens. Log in with your paid Claude account and approve the request — same flow as Step 6.

5. Back in VS Code, try a message in the chat panel, e.g. *"What files are in this project?"* When Claude proposes edits, they render as inline diffs in the panel — click a diff to expand it, then accept or reject from the panel itself.

Notes:
- **Pin the panel so it survives restarts:** open VS Code settings (`Cmd+,`), search for `claudeCode.preferredLocation`, and set it to **sidebar**. Without this, the panel can disappear when you reload the window.
- **CLI and extension don't always share credentials.** If the panel shows a sign-in screen even after Step 6, that's expected — just sign in once more from the panel.
- **Requires VS Code 1.98 or higher.** If you installed VS Code via brew in Step 1, you're already current.
- **Open files with `@`:** in the panel's prompt box, type `@` to fuzzy-search files in your project. This is faster and more reliable than pasting paths.

---

## Quick reference

| Goal | Command |
|------|---------|
| Check a tool is installed | `git --version`, `node --version`, etc. |
| See where a command lives | `which claude` |
| Claude Code health check | `claude doctor` |
| Update Claude Code | auto-updates in the background |
| Update brew packages | `brew upgrade` |
| Start Claude Code | `claude` (from the project folder) |
| Exit Claude Code | `/exit` |
| Open Claude Code panel | Click ✱ in Activity Bar, or `Cmd+Shift+P` → "Claude Code" |

---

## Troubleshooting

- **A command "is not recognized" right after installing it** — almost always a stale PATH. Quit Terminal completely (`Cmd+Q`) and open a fresh window.
- **`claude` still not found after the PATH fix** — confirm the binary exists with `test -f ~/.local/bin/claude && echo "exists"`. If it prints `exists`, you have a stale terminal; if not, re-run the Step 3 installer.
- **Browser login gets stuck in a loop** — try a different browser for the initial sign-in (Safari, Chrome, Firefox), or temporarily relax strict tracker/cookie blocking.
- **Claude Code panel disappears after restarting VS Code** — set `claudeCode.preferredLocation` to `sidebar` in VS Code settings (`Cmd+,`).
- **Spark icon missing from the Activity Bar** — confirm the extension is published by **Anthropic** (not a similarly-named third-party), and reload the window from the Command Palette: **Developer: Reload Window**.
- **`brew install` fails with a permissions error** — usually means Homebrew was installed under a different user, or `/opt/homebrew` (or `/usr/local`) has wrong ownership. Run `sudo chown -R $(whoami) $(brew --prefix)/*` to fix it.