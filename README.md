# Factorio Server (Debian)

Create a factorio user.

```sh
adduser --disable-login --gecos factorio factorio
```

Install headless server to `/opt/factorio`.

```sh
chown -R factorio:factorio /opt/factorio
```

Edit `config-path.cfg` and set the variable `config-path` to `/home/factorio`.

Create a new map or use an existing one and put it to `/home/factorio/saves/map.zip`

Edit `server-settings.json`.

```sh
systemctl start factorio.service
systemctl enable factorio.service
```

Use a rcon-client (like https://github.com/itzg/rcon-cli) or the built-in command line to set admin permissions if needed.

```
/permit username
```

# Gnome Launcher

Put the `factorio.desktop` to `/home/username/.local/share/applications/` and edit the path to point to the icon and binary.