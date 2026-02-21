import os
import datetime
import gi
import shutil

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf

# 分割したファイルをインポート
import config
from x11_helper import X11Helper
import animation

class ModernDock(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_title("Modern Dock")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        
        # X11ヘルパーの初期化
        self.x11 = X11Helper()
        
        # 初期サイズ設定
        self.dock_w = 0
        self.update_geometry()

        # ウィンドウ設定
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.stick()
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        # 透過設定
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual and self.get_screen().is_composited():
            self.set_visual(visual)

        # CSS設定
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), 
            self.css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.settings = Gtk.Settings.get_default()
        self.settings.connect("notify::gtk-theme-name", lambda s, p: self.update_css())
        self.update_css()
        
        # アイコン関連
        self.icon_theme = Gtk.IconTheme.get_default()
        self.icon_cache = {}
        self.build_icon_cache()

        # 実行中のアニメーション保持用
        self.running_animations = []
            
        # --- レイアウト構築 ---
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.get_style_context().add_class("dock-container")
        self.add(self.main_box)
        
        self._setup_launcher()
        self._setup_taskbar()
        self._setup_status_area()
        
        # 定期実行タスク
        GLib.timeout_add_seconds(1, self.update_clock)
        
        # X11イベント監視を開始
        if self.x11.enabled:
            self.x11.start_monitoring(self.update_window_list)
            # 初回描画
            self.update_window_list()

        self.connect("realize", lambda w: self.align_to_bottom())
        self.connect("map-event", lambda w, e: self.align_to_bottom())
        self.show_all()

    def _setup_launcher(self):
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        left_box.set_valign(Gtk.Align.CENTER)
        self.launcher_btn = Gtk.Button()
        self.launcher_btn.get_style_context().add_class("launcher-button")
        launcher_icon = Gtk.Image.new_from_icon_name("view-app-grid-symbolic", Gtk.IconSize.MENU)
        self.launcher_btn.add(launcher_icon)
        self.launcher_btn.connect("clicked", self.on_launcher_clicked)
        left_box.pack_start(self.launcher_btn, False, False, 0)
        self.main_box.pack_start(left_box, False, False, 0)

    def _setup_taskbar(self):
        self.center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.center_box.set_halign(Gtk.Align.CENTER)
        self.center_box.set_valign(Gtk.Align.CENTER)
        self.main_box.pack_start(self.center_box, True, False, 0)

    def _setup_status_area(self):
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        right_box.set_valign(Gtk.Align.CENTER)
        status_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_container.get_style_context().add_class("status-pill")
        self.clock_label = Gtk.Label(label="00:00")
        self.clock_label.get_style_context().add_class("clock-label")
        status_container.pack_end(self.clock_label, False, False, 0)
        for icon in ["audio-volume-medium-symbolic", "network-wireless-symbolic"]:
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
            img.get_style_context().add_class("status-icon")
            status_container.pack_end(img, False, False, 0)
        right_box.pack_start(status_container, False, False, 0)
        self.main_box.pack_start(right_box, False, False, 0)

    def update_css(self):
        is_dark = self._is_dark_theme()
        theme_colors = config.COLORS["dark"] if is_dark else config.COLORS["light"]
        radius = int(config.DOCK_HEIGHT * config.RADIUS_RATIO)
        btn_padding = int(config.DOCK_HEIGHT * 0.1)
        control_height = int(config.DOCK_HEIGHT * config.CONTROL_RATIO)
        css = f"""
        window {{ background-color: transparent; }}
        .dock-container {{
            background-color: {theme_colors["bg"]};
            border-radius: {radius}px {radius}px 0px 0px; 
            padding: 0px 10px;
        }}
        .app-button {{
            background-color: transparent;
            border: none;
            padding: {btn_padding}px;
            border-radius: 12px;
            margin: 0 4px;
            transition: background-color 200ms;
        }}
        .app-button:hover {{ background-color: {theme_colors["hover"]}; }}
        .launcher-button {{
            background-color: transparent;
            border: none;
            border-radius: 50%;
            min-width: {int(config.DOCK_HEIGHT * 0.7)}px;
            min-height: {int(config.DOCK_HEIGHT * 0.7)}px;
        }}
        .clock-label {{
            font-size: {int(config.DOCK_HEIGHT * 0.25)}px;
            font-weight: 500;
            color: {theme_colors["text"]};
        }}
        .status-pill {{
            background-color: {theme_colors["hover"]};
            border-radius: 20px;
            padding: 0px 12px;
            min-height: {control_height}px;
        }}
        .status-icon {{ color: {theme_colors["text"]}; opacity: 0.8; }}
        """
        self.css_provider.load_from_data(css.encode('utf-8'))

    def update_geometry(self):
        gdk_display = Gdk.Display.get_default()
        monitor = gdk_display.get_primary_monitor() or gdk_display.get_monitor(0)
        rect = monitor.get_geometry()
        self.dock_w = int(rect.width * config.WIDTH_RATIO)
        self.set_default_size(self.dock_w, config.DOCK_HEIGHT)

    def align_to_bottom(self):
        gdk_display = Gdk.Display.get_default()
        monitor = gdk_display.get_primary_monitor() or gdk_display.get_monitor(0)
        geo = monitor.get_geometry()
        x = geo.x + (geo.width - self.dock_w) // 2
        y = geo.y + geo.height - config.DOCK_HEIGHT
        self.move(x, y)
        self.resize(self.dock_w, config.DOCK_HEIGHT)
        if self.x11.enabled:
            try:
                win_id = self.get_window().get_xid()
                self.x11.set_strut(win_id, x, y, self.dock_w, config.DOCK_HEIGHT, geo.width, geo.height)
                # ここで自分自身にドック設定と独自の識別タグを付与！
                self.x11.set_dock_properties(win_id)
            except Exception as e:
                print(f"Failed to set X11 properties: {e}")
        return False

    def build_icon_cache(self):
        apps = Gio.AppInfo.get_all()
        for app in apps:
            icon = app.get_icon()
            if not icon: continue
            icon_str = icon.to_string()
            if app.get_id(): 
                self.icon_cache[app.get_id().lower().replace(".desktop","")] = icon_str
            if app.get_executable():
                try: 
                    self.icon_cache[os.path.basename(app.get_executable()).lower()] = icon_str
                except: pass
            if isinstance(app, Gio.DesktopAppInfo) and app.get_startup_wm_class():
                self.icon_cache[app.get_startup_wm_class().lower()] = icon_str

    def load_icon_pixbuf(self, icon_string, size):
        if not icon_string: return None
        try:
            if self.icon_theme.has_icon(icon_string):
                return self.icon_theme.load_icon(icon_string, size, Gtk.IconLookupFlags.FORCE_SIZE)
            elif os.path.exists(icon_string):
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_string, size, size, True)
            return self.icon_theme.load_icon("application-default-icon", size, 0)
        except: return None

    def update_window_list(self):
        """ウィンドウリストを更新する（独自のタグをチェックして自分を除外する）"""
        window_ids = self.x11.get_window_list()
        current_buttons = {}
        for child in self.center_box.get_children():
            if hasattr(child, 'win_id'):
                current_buttons[child.win_id] = child

        # 削除処理
        for win_id, btn in list(current_buttons.items()):
            if win_id not in window_ids:
                if config.ANIMATION_ENABLED:
                    del current_buttons[win_id]
                    del btn.win_id 
                    self._animate_button_exit(btn)
                else:
                    self.center_box.remove(btn)
                    del current_buttons[win_id]

        # 追加処理
        icon_size = int(config.DOCK_HEIGHT * 0.7)
        for win_id in window_ids:
            if win_id in current_buttons: continue

            # --- ここで「無視すべきウィンドウか（自分自身か）」をチェック ---
            if self.x11.is_ignored_window(win_id):
                continue

            try:
                app_class = self.x11.get_window_class(win_id)
                if not app_class: continue
                
                # 念のため名前でも追加チェック
                if app_class in ["desktop_window", "dock", "gnome-shell", "xfce4-panel"]: continue

                icon_str = self._get_icon_string_for_class(app_class)
                pixbuf = self.load_icon_pixbuf(icon_str, icon_size)

                btn = Gtk.Button()
                btn.get_style_context().add_class("app-button")
                btn.win_id = win_id
                img = Gtk.Image()
                if pixbuf: img.set_from_pixbuf(pixbuf)
                btn.add(img)
                btn.connect("clicked", self.on_task_button_clicked, win_id)
                self.center_box.pack_start(btn, False, False, 0)
                btn.show_all()
                if config.ANIMATION_ENABLED: self._animate_button_entry(btn)
            except Exception as e:
                print(f"Error adding button: {e}")
        return True

    def _animate_button_entry(self, widget):
        easing_func = getattr(animation.Easing, config.ANIMATION_EASING, animation.Easing.ease_out_quad)
        widget.set_opacity(0.0)
        def on_update(val): widget.set_opacity(val)
        anim = animation.Animator(duration_ms=config.ANIMATION_DURATION, update_callback=on_update, complete_callback=lambda: widget.set_opacity(1.0), easing_func=easing_func)
        anim.start()
        self.running_animations.append(anim)

    def _animate_button_exit(self, widget):
        easing_func = getattr(animation.Easing, config.ANIMATION_EASING, animation.Easing.ease_out_quad)
        def on_update(val): widget.set_opacity(1.0 - val)
        def on_complete():
            self.center_box.remove(widget)
            widget.destroy()
        anim = animation.Animator(duration_ms=config.ANIMATION_DURATION, update_callback=on_update, complete_callback=on_complete, easing_func=easing_func)
        anim.start()
        self.running_animations.append(anim)

    def on_task_button_clicked(self, button, win_id):
        active_id = self.x11.get_active_window()
        if active_id == win_id: self.x11.minimize_window(win_id)
        else: self.x11.activate_window(win_id)

    def _get_icon_string_for_class(self, name):
        mapping = {"gnome-terminal-server": "utilities-terminal", "code": "vscode"}
        if name in mapping: return mapping[name]
        if name in self.icon_cache: return self.icon_cache[name]
        return name

    def update_clock(self):
        self.clock_label.set_text(datetime.datetime.now().strftime("%H:%M"))
        return True

    def _is_dark_theme(self):
        try:
            theme = self.settings.get_property("gtk-theme-name").lower()
            return "dark" in theme or self.settings.get_property("gtk-application-prefer-dark-theme")
        except: return False

    def on_launcher_clicked(self, button):
        launcher_cmd = getattr(config, 'LAUNCHER_CMD')
        try:
            executable = launcher_cmd.split()[0]
            if shutil.which(executable):
                GLib.spawn_command_line_async(launcher_cmd)
                return
        except Exception as e: print(f"Direct execution failed: {e}")
        desktop_id = launcher_cmd if launcher_cmd.endswith(".desktop") else f"{launcher_cmd}.desktop"
        app_info = Gio.DesktopAppInfo.new(desktop_id)
        if app_info:
            try: app_info.launch([], Gdk.AppLaunchContext())
            except Exception as e: print(f"Desktop launch error: {e}")