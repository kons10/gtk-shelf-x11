import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# X11操作用ライブラリの読み込みを試みる
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
        if self.enabled:
            try:
                self.display = display.Display()
                self.root = self.display.screen().root
                
                # よく使うAtomを事前登録
                self.atom_client_list = self.display.intern_atom('_NET_CLIENT_LIST')
                self.atom_active_window = self.display.intern_atom('_NET_ACTIVE_WINDOW')
                self.atom_wm_change_state = self.display.intern_atom('WM_CHANGE_STATE')
                
                # Strut (場所取り) 用のAtom
                self.atom_strut = self.display.intern_atom('_NET_WM_STRUT')
                self.atom_strut_partial = self.display.intern_atom('_NET_WM_STRUT_PARTIAL')
                self.atom_cardinal = self.display.intern_atom('CARDINAL')
                
                # ウィンドウのタイプと状態用のAtom (ドック設定用)
                self.atom_window_type = self.display.intern_atom('_NET_WM_WINDOW_TYPE')
                self.atom_type_dock = self.display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
                self.atom_wm_state = self.display.intern_atom('_NET_WM_STATE')
                self.atom_state_skip_taskbar = self.display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR')
                self.atom_state_skip_pager = self.display.intern_atom('_NET_WM_STATE_SKIP_PAGER')
                self.atom_atom = self.display.intern_atom('ATOM')
                
                # 自分を識別するための独自のAtom（タグ）
                self.atom_skip_shelf = self.display.intern_atom('_GTK_SHELF_SKIP')
                
            except Exception as e:
                print(f"X11 init failed: {e}")
                self.enabled = False

    def start_monitoring(self, callback):
        """X11のイベント監視を開始する (GLibのループに統合)"""
        if not self.enabled: return

        self.callback = callback
        
        # ルートウィンドウのプロパティ変更（ウィンドウリストやアクティブウィンドウの変化）を監視
        self.root.change_attributes(event_mask=X.PropertyChangeMask)
        
        # X11のソケットをGLibで監視する
        try:
            fd = self.display.display.socket.fileno()
            GLib.io_add_watch(fd, GLib.IO_IN, self._on_x_event)
            print("X11 event monitoring started.")
        except Exception as e:
            print(f"Failed to start X11 monitoring: {e}")

    def _on_x_event(self, source, condition):
        """X11からイベントが来たときに呼ばれる"""
        try:
            while self.display.pending_events() > 0:
                event = self.display.next_event()
                if event.type == X.PropertyNotify:
                    if event.atom in [self.atom_client_list, self.atom_active_window]:
                        if self.callback:
                            self.callback()
        except Exception as e:
            print(f"Error in event loop: {e}")
        return True

    def set_dock_properties(self, win_id):
        """ウィンドウをドックとして設定し、独自の識別タグも付与する"""
        if not self.enabled: return

        try:
            window = self.display.create_resource_object('window', win_id)
            
            # 標準的なドック設定
            window.change_property(self.atom_window_type, self.atom_atom, 32, [self.atom_type_dock])
            window.change_property(self.atom_wm_state, self.atom_atom, 32, [self.atom_state_skip_taskbar, self.atom_state_skip_pager])
            
            # 独自の識別用タグを付与 (1を設定)
            window.change_property(self.atom_skip_shelf, self.atom_cardinal, 32, [1])
            
            self.display.flush()
        except Exception as e:
            print(f"Error setting dock properties: {e}")

    def is_ignored_window(self, win_id):
        """指定したウィンドウが、自分自身（またはドック）であるかチェックする"""
        if not self.enabled: return False
        
        try:
            win = self.display.create_resource_object('window', win_id)
            
            # 独自のタグが付いているか確認
            prop = win.get_full_property(self.atom_skip_shelf, self.atom_cardinal)
            if prop and prop.value and prop.value[0] == 1:
                return True
                
            # または、標準的なドックタイプであるか確認
            type_prop = win.get_full_property(self.atom_window_type, self.atom_atom)
            if type_prop and self.atom_type_dock in type_prop.value:
                return True
                
        except:
            pass
        return False

    def set_strut(self, win_id, x, y, width, height, screen_width, screen_height):
        """ウィンドウマネージャーにドックの領域（Strut）を予約する"""
        if not self.enabled: return

        try:
            window = self.display.create_resource_object('window', win_id)
            strut_partial = [0, 0, 0, height, 0, 0, 0, 0, 0, 0, x, x + width]
            strut = [0, 0, 0, height]
            window.change_property(self.atom_strut_partial, self.atom_cardinal, 32, strut_partial)
            window.change_property(self.atom_strut, self.atom_cardinal, 32, strut)
            self.display.flush()
        except Exception as e:
            print(f"Error setting strut: {e}")

    def get_window_list(self):
        if not self.enabled: return []
        try:
            prop = self.root.get_full_property(self.atom_client_list, X.AnyPropertyType)
            if not prop: return []
            return prop.value
        except Exception as e:
            print(f"Error getting window list: {e}")
            return []

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
        except Exception as e:
            print(f"Error getting active window: {e}")
        return None

    def activate_window(self, win_id):
        if not self.enabled: return
        try:
            win = self.display.create_resource_object('window', win_id)
            data = [2, X.CurrentTime, 0, 0, 0]
            ev = xevent.ClientMessage(window=win, client_type=self.atom_active_window, data=(32, data))
            self.root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            self.display.flush()
        except Exception as e:
            print(f"Error activating window: {e}")

    def minimize_window(self, win_id):
        if not self.enabled: return
        try:
            win = self.display.create_resource_object('window', win_id)
            data = [3, 0, 0, 0, 0]
            ev = xevent.ClientMessage(window=win, client_type=self.atom_wm_change_state, data=(32, data))
            self.root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            self.display.flush()
        except Exception as e:
            print(f"Error minimizing window: {e}")