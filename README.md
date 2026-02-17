# gtk-shelf-x11

![video gif](https://github.com/user-attachments/assets/3e0365d2-7ddd-4371-8bcd-01a97d692acc)

A lightweight and modern desktop shelf for Linux (X11).
It is built using a combination of GTK3 and Xlib, and is specifically designed to run smoothly with window managers such as Openbox.


## Features


- **Modern Design**: A stylish appearance featuring rounded corners, transparent backgrounds, and hover animations.
- **Window List**: Displays running applications in real time and allows you to activate a window by clicking it.
- **App Launcher**: You can launch your favorite launcher by left-clicking.
- **Status Display**: ~~Compactly displays network, volume, and clock information.~~ Not implemented, sorry.
- **Openbox Optimization**: Successfully fixed the shelf at the bottom at the x11 level.



## Required Packages

### Arch-based systems

The following packages are essential:

```bash
sudo pacman -S python-gobject python-xlib gtk3 roboto-fonts
```

### Debian-based systems

The following packages are essential:

```bash
sudo apt install python3-gi python3-xlib gir1.2-gtk-3.0 fonts-roboto
```

### Red Hat-based systems

The following packages are essential:

```bash
sudo dnf install python3-gobject python3-xlib gtk3 roboto-fonts
```

Additionally, we recommend using **Papirus** as the icon theme.


## How to Use

Please clone or download this repository and run it in Python.

```bash
python3 main.py
```

## Settings


Currently, the following settings are configured using variables within the code:


* **Launcher**: Configured to call `io.github.libredeb.lightpad`.
* **Appearance**: You can freely change colors and opacity by modifying the CSS within the `load_css()` method.


## License
GNU GPL 3.0
