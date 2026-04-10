# TimeSaver

A macOS CLI tool that blocks distracting websites based on time-of-day schedules by modifying `/etc/hosts`.

## Installation

### Via Homebrew (recommended)

```bash
brew tap conorliv/timesaver
brew install timesaver
```

### Via pip/uv

```bash
# Using uv
uv tool install timesaver

# Using pip
pip install timesaver
```

### From source

```bash
git clone https://github.com/conorliv/timesaver.git
cd timesaver
uv sync
uv run timesaver --help
```

## Usage

### Add sites to block

```bash
# Add individual sites
timesaver add twitter.com
timesaver add reddit.com

# Add preset categories
timesaver preset social    # Twitter, Facebook, Instagram, TikTok, Reddit, etc.
timesaver preset news      # HackerNews, CNN, BBC, NYTimes, etc.
timesaver preset all       # All of the above
```

### Set up schedules

```bash
# Block during work hours (9 AM to 5 PM)
timesaver schedule add 09:00 17:00

# Block overnight (10 PM to 6 AM) - supports crossing midnight
timesaver schedule add 22:00 06:00

# View schedules
timesaver schedule list

# Clear all schedules (blocks 24/7 when enabled)
timesaver schedule clear
```

### Enable/disable blocking

```bash
# Enable blocking (requires sudo to modify /etc/hosts)
sudo timesaver enable

# Disable blocking
sudo timesaver disable

# Check status
timesaver status
```

### Background daemon

For automatic blocking based on schedule:

```bash
# Install the launchd daemon (runs every minute)
timesaver install-daemon

# Uninstall
timesaver uninstall-daemon
```

## Commands

| Command | Description |
|---------|-------------|
| `timesaver add <url>` | Add site to block list |
| `timesaver remove <url>` | Remove site from block list |
| `timesaver list` | Show all blocked sites |
| `timesaver preset <name>` | Add preset (social, news, all) |
| `timesaver schedule add <start> <end>` | Add schedule (e.g., 09:00 17:00) |
| `timesaver schedule list` | Show schedules |
| `timesaver schedule clear` | Remove all schedules |
| `timesaver status` | Show blocking status |
| `timesaver enable` | Enable blocking (requires sudo) |
| `timesaver disable` | Disable blocking (requires sudo) |
| `timesaver install-daemon` | Install launchd service |
| `timesaver uninstall-daemon` | Uninstall launchd service |

## How it works

TimeSaver modifies your `/etc/hosts` file to redirect blocked domains to `127.0.0.1`. When blocking is enabled, entries like this are added:

```
# TIMESAVER-START
127.0.0.1 twitter.com
127.0.0.1 www.twitter.com
127.0.0.1 reddit.com
127.0.0.1 www.reddit.com
# TIMESAVER-END
```

The optional background daemon checks every minute if the current time is within a scheduled blocking period and automatically applies or removes blocks.

## Configuration

Configuration is stored in `~/.timesaver/config.json`:

```json
{
  "blocked_sites": ["twitter.com", "reddit.com"],
  "schedules": [
    {"start": "09:00", "end": "17:00"}
  ],
  "enabled": true
}
```

## License

MIT
