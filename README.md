# SP24 University Schedules TG Bot
Telegram bot schedules for the SP-24 group of Donetsk National Technical University

## Running

For the first setup, create the ignored local configuration and add the bot
token to it:

```bash
cp config.example.py config.py
```

Activate the virtual environment, then run the bot with Python or execute the
entry point directly:

```bash
source .venv/bin/activate
python3 main.py
# or
./main.py
```

Do not run `main.py` with `sh` or `bash`: it is a Python program, not a shell
script.

## systemd service

The bot runs as the `sp24-schedule-bot.service` user service. Useful commands:

```bash
systemctl --user status sp24-schedule-bot.service
systemctl --user restart sp24-schedule-bot.service
journalctl --user -u sp24-schedule-bot.service -f
```
