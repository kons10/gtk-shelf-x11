import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# X11操作用ライブラリの読み込み
try:
    from Xlib import display, X
    from Xlib.protocol import event as xevent
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False
    print("Warning: python-xlib not found. Window management features disabled.")

class X11Helper:
    def __init__(self):
        self.enabled = HAS_XLIB
        self.callback = None
        self._ignore_cache = {}
        
        if self.enabled:
            try:
                self.display = display.Display()
                self.root = self.display.screen().root
                
                # よく使うAtomを事前登録
                self.atom_client_list = self.display.intern_atom('_NET_CLIENT_LIST')
                self.atom_active_window = self.display.intern_atom('_NET_ACTIVE_WINDOW')
                self.atom_wm_change_state = self.display.intern_atom('WM_CHANGE_STATE')
                self.atom_wm_name = self.display.intern_atom('_NET_WM_NAME')
                self.atom_utf8_string = self.display.intern_atom('UTF8_STRING')
                
                # Strut用
                self.atom_strut = self.display.intern_atom('_NET_WM_STRUT')
                self.atom_strut_partial = self.display.intern_atom('_NET_WM_STRUT_PARTIAL')
                self.atom_cardinal = self.display.intern_atom('CARDINAL')
                
                # ウィンドウタイプ
                self.atom_window_type = self.display.intern_atom('_NET_WM_WINDOW_TYPE')
                self.atom_type_dock = self.display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
                self.atom_type_desktop = self.display.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP')
                self.atom_wm_state = self.display.intern_atom('_NET_WM_STATE')
                self.atom_state_skip_taskbar = self.display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR')
                self.atom_state_skip_pager = self.display.intern_atom('_NET_WM_STATE_SKIP_PAGER')
                self.atom_atom = self.display.intern_atom('ATOM')
                self.atom_skip_shelf = self.display.intern_atom('_GTK_SHELF_SKIP')
                
            except Exception as e:
                print(f"X11 init failed: {e}")
                self.enabled = False

    def start_monitoring(self, callback):
        if not self.enabled: return
        self.callback = callback
        self.root.change_attributes(event_mask=X.PropertyChangeMask)
        try:
            fd = self.display.display.socket.fileno()
            GLib.io_add_watch(fd, GLib.IO_IN, self._on_x_event)
        except Exception as e:
            print(f"Failed to start X11 monitoring: {e}")

    def _on_x_event(self, source, condition):
        try:
            needs_update = False
            while self.display.pending_events() > 0:
                event = self.display.next_event()
                if event.type == X.PropertyNotify:
                    if event.atom in [self.atom_client_list, self.atom_active_window]:
                        needs_update = True
            
            if needs_update and self.callback:
                self.callback()
        except: pass
        return True

    def get_window_name(self, win_id):
        """指定されたウィンドウのタイトルを取得する（最新の状態をその場で取得）"""
        if not self.enabled: return "Unknown"
        try:
            win = self.display.create_resource_object('window', win_id)
            # まずはUTF-8で取得を試みる
            prop = win.get_full_property(self.atom_wm_name, self.atom_utf8_string)
            if prop and prop.value:
                return prop.value.decode('utf-8')
            # 失敗したら標準のWM_NAMEを試す
            return win.get_wm_name() or "Window"
        except:
            return "Window"

    def set_dock_properties(self, win_id):
        if not self.enabled: return
        try:
            window = self.display.create_resource_object('window', win_id)
            window.change_property(self.atom_window_type, self.atom_atom, 32, [self.atom_type_dock])
            window.change_property(self.atom_wm_state, self.atom_atom, 32, [self.atom_state_skip_taskbar, self.atom_state_skip_pager])
            window.change_property(self.atom_skip_shelf, self.atom_cardinal, 32, [1])
            self.display.flush()
        except: pass

    def is_ignored_window(self, win_id):
        if not self.enabled: return False
        if win_id in self._ignore_cache: return self._ignore_cache[win_id]
        try:
            win = self.display.create_resource_object('window', win_id)
            prop = win.get_full_property(self.atom_skip_shelf, self.atom_cardinal)
            if prop and prop.value and prop.value[0] == 1:
                self._ignore_cache[win_id] = True
                return True
            type_prop = win.get_full_property(self.atom_window_type, self.atom_atom)
            if type_prop and type_prop.value:
                if self.atom_type_dock in type_prop.value or self.atom_type_desktop in type_prop.value:
                    self._ignore_cache[win_id] = True
                    return True
            state_prop = win.get_full_property(self.atom_wm_state, self.atom_atom)
            if state_prop and state_prop.value:
                if self.atom_state_skip_taskbar in state_prop.value:
                    self._ignore_cache[win_id] = True
                    return True
        except: pass
        return False

    def clear_cache(self, current_ids):
        dead_ids = [wid for wid in self._ignore_cache if wid not in current_ids]
        for wid in dead_ids:
            del self._ignore_cache[wid]

    def set_strut(self, win_id, x, y, width, height, screen_width, screen_height):
        if not self.enabled: return
        try:
            window = self.display.create_resource_object('window', win_id)
            strut_partial = [0, 0, 0, height, 0, 0, 0, 0, 0, 0, x, x + width]
            strut = [0, 0, 0, height]
            window.change_property(self.atom_strut_partial, self.atom_cardinal, 32, strut_partial)
            window.change_property(self.atom_strut, self.atom_cardinal, 32, strut)
            self.display.flush()
        except: pass

    def get_window_list(self):
        if not self.enabled: return []
        try:
            prop = self.root.get_full_property(self.atom_client_list, X.AnyPropertyType)
            if not prop: return []
            return prop.value
        except: return []

    def get_window_class(self, win_id):
        if not self.enabled: return None
        try:
            win = self.display.create_resource_object('window', win_id)
            wm_class = win.get_wm_class()
            if wm_class: return wm_class[1].lower()
        except: pass
        return None

    def get_active_window(self):
        if not self.enabled: return None
        try:
            prop = self.root.get_full_property(self.atom_active_window, X.AnyPropertyType)
            if prop and prop.value: return prop.value[0]
        except: return None

    def activate_window(self, win_id):
        if not self.enabled: return
        try:
            win = self.display.create_resource_object('window', win_id)
            data = [2, X.CurrentTime, 0, 0, 0]
            ev = xevent.ClientMessage(window=win, client_type=self.atom_active_window, data=(32, data))
            self.root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            self.display.flush()
        except: pass

    def minimize_window(self, win_id):
        if not self.enabled: return
        try:
            win = self.display.create_resource_object('window', win_id)
            data = [3, 0, 0, 0, 0]
            ev = xevent.ClientMessage(window=win, client_type=self.atom_wm_change_state, data=(32, data))
            self.root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            self.display.flush()
        except: pass