# gtk-shelf-x11

![video gif](https://github.com/user-attachments/assets/3e0365d2-7ddd-4371-8bcd-01a97d692acc)

A lightweight and modern desktop shelf for Linux (X11) built with GTK3 and Python. It provides a functional taskbar and application launcher with a focus on aesthetics and smooth interaction, specifically optimized for window managers like Openbox and Many WM.

## Features

- **Modern & Adaptive UI**: Features a sleek design with rounded corners and transparent backgrounds that automatically adjust based on your system's light or dark theme.
- **Smart Window Management**: 
  - Real-time window list tracking using X11 event monitoring.
  - Click to activate/focus or minimize windows.
  - Filtered taskbar that excludes system components like desktop backgrounds and panels.
- **Dynamic Animations**: Smooth button entry effects using configurable easing functions (e.g., `ease_out_back`) for a "pop" feel.
- **Integrated Launcher**: Supports launching applications via commands (like `rofi`) or `.desktop` files.
- **System Status & Clock**: Displays a live clock and status icons in a stylized "pill" container.
- **WM Optimization**: Uses EWMH Struts to reserve screen space, ensuring windows don't overlap with the dock.

## Required Packages

### Arch-based systems
```bash
sudo pacman -S python-gobject python-xlib gtk3 roboto-fonts

```

### Debian-based systems

```bash
sudo apt install python3-gi python3-xlib gir1.2-gtk-3.0 fonts-roboto

```

### Red Hat-based systems

```bash
sudo dnf install python3-gobject python3-xlib gtk3 roboto-fonts

```

*Note: **Papirus** is the recommended icon theme for the best visual experience.*

## How to Use

Clone the repository and run the application using Python:

```bash
python3 main.py

```

## Configuration

You can customize the dock by editing `config.py`. Key settings include:

* **Appearance**: Adjust `DOCK_HEIGHT`, `WIDTH_RATIO`, and `RADIUS_RATIO`.
* **Launcher**: Set your preferred launcher command in `LAUNCHER_CMD` (defaults to `rofi`).
* **Animations**: Toggle `ANIMATION_ENABLED` or change the `ANIMATION_EASING` style (e.g., `linear`, `ease_out_quad`, `ease_out_back`).
* **Colors**: Customize the RGBA values for both light and dark modes.

## License

GNU GPL 3.0
