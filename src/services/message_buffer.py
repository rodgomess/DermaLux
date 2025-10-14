import threading

class MessageBuffer:
    def __init__(self, idle_window=5, max_parts=20, max_chars=1000):
        self.max_chars = max_chars
        self.max_parts = max_parts
        self.idle_window = idle_window
        self.buffers = {}
        self.timers = {}
        self.lock = threading.RLock()

    def add(self, phone, text, on_flush):
        with self.lock:
            parts = self.buffers.setdefault(phone, [])
            parts.append(text)

            # hard caps
            if len(parts) >= self.max_parts or sum(len(p) for p in parts) >= self.max_chars:
                # flush imediato se estourou limites
                self.flush(phone, on_flush)
                return
            
            # (re)arma timer
            old = self.timers.get(phone)
            if old: old.cancel()
            t = threading.Timer(self.idle_window, self.flush, args=(phone, on_flush))
            t.daemon = True
            self.timers[phone] = t
            t.start()

    def flush(self, phone, on_flush):
        with self.lock:
            parts = self.buffers.pop(phone, [])
            t = self.timers.pop(phone, None)
            if t: t.cancel()
        if not parts:
            return
        text = " ".join(p.strip() for p in parts if p.strip())
        if text:
            on_flush(phone, text)