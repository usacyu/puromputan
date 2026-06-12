import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as fd
import threading, requests, base64, datetime, os, subprocess, json, io, webbrowser
from PIL import Image
from http.server import HTTPServer, BaseHTTPRequestHandler

# ══════════════════════════════════════════════
#  ぷろんぷたん 🎀  公開版  v1.0
#  AI → SD Prompt Bridge Tool
# ══════════════════════════════════════════════

PORT_RANGE_START = 7871
PORT_RANGE_END   = 7880
CONFIG_FILE      = "config.json"

def find_available_port():

    import socket
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port)); return port
        except OSError:
            continue
    return PORT_RANGE_START

# ── カラーパレット（上品カワイイ）────────────────────
#   既存の定数名は維持し、値だけ刷新。未改修コードも自動で新配色に揃う。
C_BG        = "#fbf7fb"   # アプリ背景（やわらかいホワイト）
C_CARD      = "#ffffff"   # カード面
C_STATUS    = "#f8f2f9"   # セクション地・サブ面
C_BORDER    = "#ece2f0"   # ヘアライン境界
C_POS       = "#ecf8f1"   # ポジ淡色
C_NEG       = "#fdebf0"   # ネガ淡色
C_GO        = "#e85d9a"   # 主役ピンク（CTA）
C_GO_H      = "#d84a88"   # 主役ホバー
C_AUTO      = "#f4a9cb"   # 自動生成ボタン
C_TEXT      = "#3a343f"   # 本文（濃インク）
C_TEXT_S    = "#8c8295"   # 副次テキスト
C_GRAY      = "#9a8fa6"
C_PURPLE    = "#7e5bb5"   # 見出し系の紫
C_ACCENT    = "#9b6bd6"   # サブ・紫アクセント
C_ACCENT_L  = "#e7d9f7"   # 紫の淡色（ホバー/地）
C_LAVENDER  = "#f1e9fb"   # 淡ラベンダー地
C_GREEN     = "#36b98b"
C_RED       = "#f0617e"
C_ORANGE    = "#f2a93c"   # 琥珀（自動/注意）
# ── 追加トークン ──
C_INK       = C_TEXT
C_SUB       = C_TEXT_S
C_FAINT     = "#b9afc2"   # キャプション/最薄
C_PINK      = C_GO
C_PINK_H    = C_GO_H
C_PINK_SOFT = "#fcebf3"   # ピンク淡色（選択地/ホバー）
C_PURPLE_S  = "#f1e9fb"   # 紫淡色

# ── アイコン（Lucide / assets.py）──
try:
    import assets as _assets
except Exception as _e:           # 取得失敗してもアプリは動かす
    _assets = None
    print(f"[app] assets読込失敗（アイコンはテキスト表示にフォールバック）: {_e}")

def ICON(name, color=C_PINK, size=18):
    """Lucideアイコンの CTkImage を返す。失敗時 None → 呼び出し側はテキスト維持。"""
    if _assets is None:
        return None
    try:
        return _assets.icon(name, color, size)
    except Exception:
        return None

# ── 言語文字列 ────────────────────────────────────
STRINGS = {
    "ja": {
        "title":            "ぷろんぷたん 🎀",
        "tab_main":         "🎀 ぷろんぷたん",
        "tab_settings":     "⚙️  設定",
        "lang_btn":         "🇬🇧 EN",
        # ステータスバー
        "sd_connected":     "🟢 SD接続中",
        "sd_disconnected":  "🔴 SD未接続",
        "sb_port":          "ポート {p}",
        "sb_starting":      "起動中...",
        "sb_mode_auto":     "⚡ 自動",
        "sb_mode_manual":   "👀 確認",
        "sb_pos_wait":      "⬜ ポジ待機中",
        "sb_pos_ok":        "✅ ポジ受信",
        "sb_neg_wait":      "⬜ ネガ待機中",
        "sb_neg_ok":        "✅ ネガ受信",
        # ステータスメッセージ
        "st_waiting":       "プロンプトを送ってね！",
        "st_pos_only":      "ポジのみ受信！ネガ待機中…",
        "st_ready":         "✅ 受信完了！生成できるよ！",
        "st_countdown":     "ポジのみ！あと {n} 秒で生成するよ！",
        "st_generating":    "🎨 生成中...！",
        "st_done_both":     "✨ ポジ＋ネガで出力したよ！",
        "st_done_pos":      "✨ ポジのみで出力したよ！",
        "st_same_prompt":   "同じプロンプトだからスキップ！（ボタンで作れるよ）",
        "st_sd_error":      "❌ SD接続エラー (コード: {c})",
        "st_sd_no_conn":    "❌ SDに繋がらないよ。起動してるか確認してね！",
        "st_gen_error":     "❌ エラー: {e}",
        "st_gen_failed":    "⚠️ 画像が返ってこなかった…",
        # 生成設定
        "gen_settings":     "生成設定",
        "quality_lbl":      "クオリティ",
        "preset_fast":      "⚡ 爆速",
        "preset_normal":    "✨ 通常",
        "preset_hq":        "💎 高品質",
        "preset_forge":     "🔄 Forge同期値",
        "forge_no_sync":    "（未同期）",
        "params_lbl":       "パラメーター",
        "mode_lbl":         "生成モード",
        "mode_auto":        "⚡ 自動\n届いたら即生成",
        "mode_manual":      "👀 確認\n手動で生成",
        # ポジネガ
        "pos_waiting":      "📗 ポジティブ　⬜ 待機中",
        "pos_received":     "📗 ポジティブ　✅ 受信済み",
        "neg_waiting":      "📕 ネガティブ　⬜ 待機中",
        "neg_received":     "📕 ネガティブ　✅ 受信済み",
        "copy":             "📋 コピー",
        "clear":            "クリア",
        # リデザイン用
        "lbl_pos":          "ポジティブ",
        "lbl_neg":          "ネガティブ",
        "pill_wait":        "待機中",
        "pill_recv":        "受信完了",
        "chip_sd_on":       "SD接続中",
        "chip_sd_off":      "SD未接続",
        "chip_busy":        "生成中",
        "s_lang_title":     "言語 / Language",
        "s_lang_ja":        "日本語",
        "s_lang_en":        "English",
        # 生成ボタン
        "go_waiting":       "生成する！\n（プロンプト待ち）",
        "go_pos_only":      "ポジのみで生成！",
        "go_manual":        "生成する！",
        "go_auto":          "自動生成中",
        # プレビュー
        "preview_lbl":      "プレビュー",
        "preview_wait":     "生成した画像が\nここに表示されるよ！",
        "history_lbl":      "最近作った絵",
        "history_empty":    "まだ画像がないよ。\n生成するとここに並ぶよ！",
        "history_hidden":   "非表示中（Hide をもう一度押すと表示）",
        "st_history_view":  "履歴の画像を表示中だよ",
        "pill_manual":      "手入力",
        "pill_used":        "生成済み",
        "prev_s": "S", "prev_m": "M", "prev_l": "L", "prev_hide": "Hide",
        "open_file":        "画像を開く",
        "open_folder":      "フォルダを開く",
        "open_manual":      "マニュアル",
        "spice_lbl":        "✨ ポジスパイス",
        "spice_none":       "なし",
        "neg_boost_btn":    "ネガ補強（手・指・足）",
        "neg_boost_added":  "✅ ネガ補強を追記したよ！",
        # 設定タブ
        "s_sd_title":       "SD接続設定",
        "s_sd_url":         "Stable Diffusion WebUI アドレス",
        "s_forge_title":    "Forge設定",
        "s_forge_btn":      "Forgeから設定を取り込む",
        "s_forge_ok":       "✅ 取り込み完了！",
        "s_forge_fail":     "❌ 取り込み失敗（Forge起動してる？）",
        "s_save_title":     "保存設定",
        "s_save_dir":       "画像の保存先フォルダ",
        "s_browse":         "フォルダ選ぶ",
        "s_params_title":   "生成パラメーター",
        "s_cfg":            "CFGスケール",
        "s_width":          "横 px",
        "s_height":         "縦 px",
        "s_anchor_title":   "検知マーカー設定",
        "s_anchor_note":    "※ 変えたらAIへのお約束も更新してね！",
        "s_pos_anchor":     "ポジティブ開始マーカー",
        "s_neg_anchor":     "ネガティブ開始マーカー",
        "s_spice_title":    "ポジスパイス設定（1〜9）",
        "s_spice_note":     "生成時にポジに追記されるよ！空欄はスキップ",
        "s_neg_title":      "ネガ補強テンプレート",
        "s_save_btn":       "保存する",
        "s_saved":          "✅ 保存したよ！",
    },
    "en": {
        "title":            "Puromputan 🎀",
        "tab_main":         "🎀 Puromputan",
        "tab_settings":     "⚙️  Settings",
        "lang_btn":         "🇯🇵 JA",
        "sd_connected":     "🟢 SD Connected",
        "sd_disconnected":  "🔴 SD Not Connected",
        "sb_port":          "Port {p}",
        "sb_starting":      "Starting...",
        "sb_mode_auto":     "⚡ Auto",
        "sb_mode_manual":   "👀 Manual",
        "sb_pos_wait":      "⬜ Pos waiting",
        "sb_pos_ok":        "✅ Pos received",
        "sb_neg_wait":      "⬜ Neg waiting",
        "sb_neg_ok":        "✅ Neg received",
        "st_waiting":       "Send a prompt!",
        "st_pos_only":      "Pos received! Waiting for neg…",
        "st_ready":         "✅ Ready to generate!",
        "st_countdown":     "Pos only! Generating in {n}s!",
        "st_generating":    "🎨 Generating...!",
        "st_done_both":     "✨ Pos+Neg output done!",
        "st_done_pos":      "✨ Pos-only output done!",
        "st_same_prompt":   "Same prompt — skipped (button remakes it!)",
        "st_sd_error":      "❌ SD error (code: {c})",
        "st_sd_no_conn":    "❌ Can't reach SD. Is it running?",
        "st_gen_error":     "❌ Error: {e}",
        "st_gen_failed":    "⚠️ No image returned…",
        "gen_settings":     "Generation Settings",
        "quality_lbl":      "Quality",
        "preset_fast":      "⚡ Fast",
        "preset_normal":    "✨ Normal",
        "preset_hq":        "💎 High Quality",
        "preset_forge":     "🔄 Forge Sync",
        "forge_no_sync":    "(not synced)",
        "params_lbl":       "Parameters",
        "mode_lbl":         "Mode",
        "mode_auto":        "⚡ Auto\nGenerates on receive",
        "mode_manual":      "👀 Manual\nConfirm before generate",
        "pos_waiting":      "📗 Positive　⬜ Waiting",
        "pos_received":     "📗 Positive　✅ Received!",
        "neg_waiting":      "📕 Negative　⬜ Waiting",
        "neg_received":     "📕 Negative　✅ Received!",
        "copy":             "📋 Copy",
        "clear":            "Clear",
        # redesign
        "lbl_pos":          "Positive",
        "lbl_neg":          "Negative",
        "pill_wait":        "Waiting",
        "pill_recv":        "Received",
        "chip_sd_on":       "SD Connected",
        "chip_sd_off":      "SD Off",
        "chip_busy":        "Generating",
        "s_lang_title":     "言語 / Language",
        "s_lang_ja":        "日本語",
        "s_lang_en":        "English",
        "go_waiting":       "Generate!\n(Waiting for prompt)",
        "go_pos_only":      "Generate pos-only!",
        "go_manual":        "Generate!",
        "go_auto":          "Auto generating",
        "preview_lbl":      "Preview",
        "preview_wait":     "Your image will\nappear here!",
        "history_lbl":      "Recent",
        "history_empty":    "No images yet.\nThey'll show up here!",
        "history_hidden":   "Hidden (press Hide again to show)",
        "st_history_view":  "Viewing a past image",
        "pill_manual":      "Manual",
        "pill_used":        "Generated",
        "prev_s": "S", "prev_m": "M", "prev_l": "L", "prev_hide": "Hide",
        "open_file":        "Open Image",
        "open_folder":      "Open Folder",
        "open_manual":      "Manual",
        "spice_lbl":        "✨ Pos Spice",
        "spice_none":       "None",
        "neg_boost_btn":    "Neg Boost (hands/fingers/feet)",
        "neg_boost_added":  "✅ Neg boost added!",
        "s_sd_title":       "SD Connection",
        "s_sd_url":         "Stable Diffusion WebUI address",
        "s_forge_title":    "Forge Settings",
        "s_forge_btn":      "Import settings from Forge",
        "s_forge_ok":       "✅ Import successful!",
        "s_forge_fail":     "❌ Import failed (Is Forge running?)",
        "s_save_title":     "Save Settings",
        "s_save_dir":       "Image save folder",
        "s_browse":         "Browse",
        "s_params_title":   "Generation Parameters",
        "s_cfg":            "CFG Scale",
        "s_width":          "Width px",
        "s_height":         "Height px",
        "s_anchor_title":   "Detection Markers",
        "s_anchor_note":    "※ Update AI prompt rules if changed!",
        "s_pos_anchor":     "Positive start marker",
        "s_neg_anchor":     "Negative start marker",
        "s_spice_title":    "Pos Spice Settings (1–9)",
        "s_spice_note":     "Appended to pos at generation. Leave blank to skip.",
        "s_neg_title":      "Neg Boost Template",
        "s_save_btn":       "Save",
        "s_saved":          "✅ Saved!",
    }
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ─── インジケーターランプ ────────────────────────────
class IndicatorLamp(tk.Canvas):
    """canvas製の丸型インジケーターランプ"""
    _C = {
        "off":    ("#888888", "#444444"),
        "green":  ("#44ee88", "#006633"),
        "red":    ("#ff5577", "#990033"),
        "orange": ("#ffaa33", "#cc6600"),
        "blue":   ("#55ccff", "#0066aa"),
    }
    def __init__(self, parent, size=14, bg=C_BG, **kw):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0, bg=bg, **kw)
        self._size   = size
        self._job    = None
        self._col    = "off"
        self._bright = True
        self._draw("off", True)

    def _draw(self, col, bright):
        self.delete("all")
        s = self._size
        main, dark = self._C.get(col, self._C["off"])
        fill = main if bright else dark
        self.create_oval(0, 0, s,   s,   fill=dark, outline="")
        self.create_oval(1, 1, s-1, s-1, fill=fill, outline="")
        if bright and col != "off":
            hs = max(2, s // 4)
            self.create_oval(3, 2, 3+hs, 2+hs, fill="white", outline="")

    def set(self, col):
        self._stop()
        self._col = col
        self._draw(col, True)

    def blink(self, col="orange"):
        self._stop()
        self._col    = col
        self._bright = True
        self._tick()

    def _tick(self):
        self._bright = not self._bright
        self._draw(self._col, self._bright)
        self._job = self.after(450, self._tick)

    def _stop(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None


# ─── HTTP サーバー ──────────────────────────────────
class PromptHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        if self.path == "/config":
            cfg = {
                "pos_start": self.server.app.config_data.get("positive_anchor", "🔴"),
                "pos_end":   self.server.app.config_data.get("positive_end",    "🟥"),
                "neg_start": self.server.app.config_data.get("negative_anchor", "🔵"),
                "neg_end":   self.server.app.config_data.get("negative_end",    "🟦"),
            }
            self._ok(json.dumps(cfg, ensure_ascii=False).encode())
        elif self.path == "/prompt":
            # Forge自動入力用：現在のプロンプトを配信（seqで新着判定）
            app = self.server.app
            data = {
                "seq":      getattr(app, "_prompt_seq", 0),
                "positive": getattr(app, "_positive", ""),
                "negative": getattr(app, "_negative", ""),
            }
            self._ok(json.dumps(data, ensure_ascii=False).encode())


    def do_POST(self):

        length = int(self.headers.get("Content-Length", 0))
        data   = json.loads(self.rfile.read(length))
        if self.path == "/prompt":
            pos = data.get("positive", "").strip()
            neg = data.get("negative", "").strip()
            if pos and neg:
                self.server.app.on_prompt_received(pos, neg)
            elif pos:
                self.server.app.after(0, self.server.app._apply_pos_only, pos)
            self._ok()
        elif self.path == "/settings":
            self.server.app.after(0, self.server.app._apply_forge_settings, data)
            self._ok()


    def do_OPTIONS(self):

        self.send_response(200)
        for h, v in [("Access-Control-Allow-Origin","*"),
                     ("Access-Control-Allow-Methods","GET,POST,OPTIONS"),
                     ("Access-Control-Allow-Headers","Content-Type")]:
            self.send_header(h, v)
        self.end_headers()


    def _ok(self, body=b"{}"):

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


    def log_message(self, *_): pass


def start_server(app):

    port = find_available_port()
    app.local_port = port
    app.after(0, app._on_port_found, port)
    server = HTTPServer(("127.0.0.1", port), PromptHandler)
    server.app = app
    server.serve_forever()


# ─── メインアプリ ────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):

        super().__init__()
        self.lang = "ja"
        self.config_data = self._load_config()

        # 状態変数
        self._positive       = ""
        self._negative       = ""
        self._pos_source     = None   # "recv"=受信 / "manual"=手入力 / "used"=生成済み（ピル表示用）
        self._neg_source     = None
        self._prev_flash_seq = 0      # ミニランプのペカー用（新着受信の検知＝_prompt_seq連動）
        self._gen_blink_job  = None   # 生成中チップの点滅タイマー
        self._gen_blink_state = False
        self._auto_generate  = True
        self._generating     = False
        self._last_gen_key   = ""
        self._last_saved_path = None
        self._last_img_bytes  = None
        self._preview_size    = "M"
        self._preview_size_info = (220, 220)
        self._preview_hidden  = False
        self._neg_skip_timer  = None
        self._neg_skip_count  = 0
        self._pending_prompt  = None  # 生成中に届いたプロンプト (pos, neg, pos_only)
        self._forge_synced    = bool(self.config_data.get("forge_steps", ""))
        self._sd_connected    = False
        self._port_num        = PORT_RANGE_START
        self.local_port       = PORT_RANGE_START
        self._lang_refs       = {}
        self._spice_checks    = {}   # スパイスチェックボックス {1: BoolVar, ...}
        self._spice_entries   = {}   # スパイス内容入力欄 {1: CTkEntry}
        self._neg_boost_on    = tk.BooleanVar(value=False)   # ネガ補強オン/オフ
        self._pos_received_time = None   # ポジ受信時刻
        self._neg_received_time = None   # ネガ受信時刻
        self._last_gen_time     = None   # 最終生成時刻
        self._spice_btns        = {}     # スパイスピルボタン {1: CTkButton}
        self._settings_win      = None   # 設定ウィンドウ
        self._spice_panel_open  = tk.BooleanVar(value=self.config_data.get("spice_panel_open_on_start", False))
        self._spice_panel_frame = None   # スパイスパネル本体
        self._mini_mode         = False
        self._normal_geo        = "1180x790"
        self._history_strip     = None   # 生成履歴ストリップ
        self._history_imgs      = []     # サムネ画像の参照保持（GC防止）
        self._history_btns      = {}     # path -> サムネボタン
        self._history_selected  = None   # 選択中サムネのパス
        self._tooltip           = None   # ホバー用ツールチップ窓
        self._mini_resize_job   = None   # ミニのリサイズ追従（デバウンス）
        self._mini_last_size    = None
        self._prompt_seq        = 0      # 受信カウンタ（Forge自動入力の新着判定用）

        self.title(self.S("title"))
        self.geometry("1180x790")
        self.minsize(1060, 720)
        self.configure(fg_color=C_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._update_mode_status()
        if self._forge_synced:
            self.after(200, self._update_forge_display)

        threading.Thread(target=start_server, args=(self,), daemon=True).start()
        threading.Thread(target=self._startup_sd_check, daemon=True).start()

    # ── 文字列ヘルパー ──────────────────────────────
    def S(self, key, **kw):

        s = STRINGS[self.lang].get(key, key)
        return s.format(**kw) if kw else s


    def _reg(self, key, fn):

        self._lang_refs[key] = fn

    # ── 設定 ────────────────────────────────────────
    def _load_config(self):

        d = {
            "sd_url":          "http://127.0.0.1:7860",
            "save_dir":        os.path.join(os.path.expanduser("~"), "Pictures", "SD_outputs"),
            "cfg":             "7",
            "width":           "1024",
            "height":          "1024",
            "steps":           "28",
            "sampler":         "DPM++ 2M Karras",
            "positive_anchor": "🔴",
            "positive_end":    "🟥",
            "negative_anchor": "🔵",
            "negative_end":    "🟦",
            # ポジスパイス（1〜9）
            "spice_1": "at the beach, ocean background",
            "spice_2": "blonde hair",
            "spice_3": "hot pants, denim shorts",
            "spice_4": "night scene, city lights",
            "spice_5": "rainy day, wet hair",
            "spice_6": "sunset, golden hour",
            "spice_7": "cherry blossoms, spring",
            "spice_8": "fantasy, magical atmosphere",
            "spice_9": "urban street, neon signs",
            # ネガ補強テンプレート
            "neg_boost": "fingers are exactly 5 on each hand, hands are anatomically correct no extra joints, feet are normal with correct toe count, extra limbs, missing limbs, fused fingers, bad anatomy",
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    d.update(json.load(f))
            except: pass
        return d


    def _save_config(self):

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, ensure_ascii=False, indent=2)

    # ── 言語切り替え ─────────────────────────────────
    def _toggle_lang(self):

        self.lang = "en" if self.lang == "ja" else "ja"
        self.title(self.S("title"))
        for fn in self._lang_refs.values():
            try: fn()
            except: pass

        # 動的ラベルも言語に合わせて更新
        self._update_mode_status()
        self._update_sd_status()
        self._update_recv_indicators(bool(self._positive), bool(self._negative))
        self._refresh_go_btn()

    # ── 起動時SD確認 ─────────────────────────────────
    def _startup_sd_check(self):

        url = self.config_data.get("sd_url", "http://127.0.0.1:7860")
        try:
            r = requests.get(f"{url}/sdapi/v1/samplers", timeout=3)
            if r.status_code == 200:
                self._sd_connected = True
                self.after(0, self._update_sd_status)
        except: pass

    # ── サーバーコールバック ──────────────────────────
    def on_prompt_received(self, pos, neg):

        self.after(0, self._apply_prompts, pos, neg)


    def _on_port_found(self, port):

        self._port_num = port
        self.port_lbl.configure(text=self.S("sb_port", p=port))

    # ── プロンプト受信 ───────────────────────────────
    def _apply_prompts(self, pos, neg):

        # 生成中でもUIと内部状態は必ず更新する（プロンプトを捨てない）
        self._cancel_neg_skip()
        self._positive = pos
        self._negative = neg
        self._pos_source = self._neg_source = "recv"
        self._prompt_seq += 1
        self._box_write(self.pos_box, pos)
        try: self.pos_box._textbox.tag_delete("spice_tag")
        except: pass
        self._box_write(self.neg_box, neg)
        self._pos_received_time = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        self._neg_received_time = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        self._update_recv_indicators(True, True)
        self._refresh_go_btn()
        if self._generating:
            self._set_status("⏳ 受信済み！生成完了後に生成するよ！", C_ORANGE)
            self._pending_prompt = (pos, neg, False)
            return
        if self._auto_generate:
            key = pos + "|||" + neg
            if key == self._last_gen_key:
                self._set_status(self.S("st_same_prompt"), C_ORANGE); return
            self._set_status(self.S("st_ready"), C_GREEN)
            self._generate()
        else:
            self._set_status(self.S("st_ready"), C_GREEN)


    def _apply_pos_only(self, pos):

        # 生成中でもUIと内部状態は必ず更新する
        if self._generating:
            self._cancel_neg_skip()
            self._positive = pos
            self._negative = ""
            self._pos_source = "recv"; self._neg_source = None
            self._prompt_seq += 1
            self._pos_received_time = __import__('datetime').datetime.now().strftime("%H:%M:%S")
            self._neg_received_time = None
            self._box_write(self.pos_box, pos)
            self._box_write(self.neg_box, "")
            self._update_recv_indicators(True, False)
            self._refresh_go_btn()
            self._set_status("⏳ 受信済み！生成完了後に生成するよ！", C_ORANGE)
            self._pending_prompt = (pos, "", True)
            return
        self._cancel_neg_skip()
        self._positive = pos
        self._negative = ""
        self._pos_source = "recv"; self._neg_source = None
        self._prompt_seq += 1
        self._pos_received_time = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        self._neg_received_time = None
        self._box_write(self.pos_box, pos)
        self._box_write(self.neg_box, "")
        self._update_recv_indicators(True, False)
        self._refresh_go_btn()
        if self._auto_generate:
            self._start_neg_skip()
        else:
            self._set_status(self.S("st_pos_only"), C_ORANGE)


    def _apply_forge_settings(self, data):

        for key in ("steps","cfg","width","height","sampler"):
            val = data.get(key)
            if val:
                self.config_data[key]             = str(val)
                self.config_data[f"forge_{key}"]  = str(val)
        self._forge_synced = True
        self._save_config()
        self._update_forge_display()
        if hasattr(self, 'setting_entries'):
            for k in ("cfg","width","height"):
                if k in self.setting_entries:
                    self.setting_entries[k].delete(0,"end")
                    self.setting_entries[k].insert(0, self.config_data.get(k,""))

    # ── ネガスキップ ─────────────────────────────────
    def _start_neg_skip(self):

        self._cancel_neg_skip()
        self._neg_skip_count = 5
        self._neg_skip_tick()


    def _neg_skip_tick(self):

        if self._negative or self._generating:
            self._cancel_neg_skip()
            if self._negative:
                self._set_status(self.S("st_ready"), C_GREEN)
            return
        if self._neg_skip_count <= 0:
            self._generate_pos_only()
            return
        self._set_status(self.S("st_countdown", n=self._neg_skip_count), C_ORANGE)
        self._neg_skip_count -= 1
        self._neg_skip_timer = self.after(1000, self._neg_skip_tick)


    def _cancel_neg_skip(self):

        if self._neg_skip_timer:
            self.after_cancel(self._neg_skip_timer)
            self._neg_skip_timer = None

    # ══════════ リデザイン用 UIヘルパー ══════════
    def _chip(self, parent, icon_name, text, color, bg=C_CARD, border=True):
        """アイコン＋ラベルの丸ピル（ステータスチップ）"""
        f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=999,
            border_width=1 if border else 0, border_color=C_BORDER)
        ico = ICON(icon_name, color, 15)
        il = ctk.CTkLabel(f, text="" if ico else "●", image=ico,
            text_color=color, font=("Yu Gothic UI", 11))
        il.pack(side="left", padx=(10, 4), pady=5)
        tl = ctk.CTkLabel(f, text=text, font=("Yu Gothic UI", 11, "bold"), text_color=color)
        tl.pack(side="left", padx=(0, 12))
        f._ic, f._tx = il, tl
        return f

    def _set_chip(self, chip, icon_name, text, color):
        ico = ICON(icon_name, color, 15)
        chip._ic.configure(image=ico, text="" if ico else "●", text_color=color)
        chip._tx.configure(text=text, text_color=color)

    def _select_row(self, parent, value, icon_name, text, sub, var, command):
        """ラジオの代わりになる選択行（アイコン＋ラベル、選択時ピンク地）"""
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=10)
        row._value = value; row._icon = icon_name
        il = ctk.CTkLabel(row, text="", image=ICON(icon_name, C_SUB, 18))
        il.pack(side="left", padx=(10, 8), pady=5)
        box = ctk.CTkFrame(row, fg_color="transparent"); box.pack(side="left", pady=3)
        tl = ctk.CTkLabel(box, text=text, font=("Yu Gothic UI", 12, "bold"), text_color=C_SUB)
        tl.pack(anchor="w")
        sl = None
        if sub:
            sl = ctk.CTkLabel(box, text=sub, font=("Yu Gothic UI", 9), text_color=C_FAINT)
            sl.pack(anchor="w")
        row._il, row._tl, row._sl = il, tl, sl
        def _click(_=None, r=row, v=value, vr=var, cmd=command):
            vr.set(v)
            if cmd: cmd()
            self._refresh_select_group(r.master, vr)
        for w in [row, il, box, tl] + ([sl] if sl else []):
            w.bind("<Button-1>", _click)
        return row

    def _refresh_select_group(self, container, var):
        cur = var.get()
        for row in container.winfo_children():
            if not hasattr(row, "_value"):
                continue
            sel = (row._value == cur)
            row.configure(fg_color=C_PINK_SOFT if sel else "transparent")
            col = C_PINK if sel else C_SUB
            row._il.configure(image=ICON(row._icon, col, 18))
            row._tl.configure(text_color=col)

    def _set_mini_dot(self, dot, icon_name, color):
        """ミニモードの極小ランプ（円アイコン＋文字）の色替え"""
        ico = ICON(icon_name, color, 11)
        dot._dot.configure(image=ico, text="" if ico else "●", text_color=color)
        dot._lbl.configure(text_color=color)

    def _flash_mini_dot(self, dot, color):
        """受信の瞬間ペカーっと点滅（白⇔色×3回→点灯で終わる）"""
        for i, delay in enumerate(range(0, 660, 110)):
            c = "#ffffff" if i % 2 == 0 else color
            self.after(delay, lambda c=c, d=dot:
                d.winfo_exists() and self._set_mini_dot(d, "circle-check", c))

    def _mark_prompts_used(self, raw_pos):
        """生成完了：使ったプロンプトが欄に残っていればピルを「生成済み」へ"""
        if self._positive != raw_pos:
            return   # 生成中に新しいプロンプトが届いてる＝そっちの表示を優先
        self._pos_source = "used"
        if self._negative:
            self._neg_source = "used"
        self._update_recv_indicators(bool(self._positive), bool(self._negative))

    def _set_gen_busy(self, busy):
        """生成ステータス表示（メイン＝点滅チップ / ミニ＝ランプ。橙=生成中→緑=完了）"""
        if hasattr(self, "gen_chip"):
            if busy:
                self._set_chip(self.gen_chip, "loader", self.S("chip_busy"), C_ORANGE)
                self.gen_chip.pack(side="left", padx=(0, 6))
                self._start_gen_blink()
            else:
                self._stop_gen_blink()
                self.gen_chip.pack_forget()
        if hasattr(self, "mini_gen_dot"):
            if busy:
                self._set_mini_dot(self.mini_gen_dot, "loader", C_ORANGE)
            elif self._last_gen_time:
                self._set_mini_dot(self.mini_gen_dot, "circle-check", C_GREEN)
            else:
                self._set_mini_dot(self.mini_gen_dot, "circle", C_FAINT)

    def _start_gen_blink(self):
        self._stop_gen_blink()
        self._gen_blink_state = False
        self._gen_blink_job = self.after(450, self._gen_blink_tick)

    def _gen_blink_tick(self):
        """生成中チップの明滅（小さくて気づきにくい対策）。生成が終われば自然停止"""
        self._gen_blink_job = None
        if not self._generating:
            return
        self._gen_blink_state = not self._gen_blink_state
        color = "#f7ce8a" if self._gen_blink_state else C_ORANGE   # 明⇔橙
        bg    = "#fdf3e3" if self._gen_blink_state else C_CARD     # 地色もふわっと
        try:
            self._set_chip(self.gen_chip, "loader", self.S("chip_busy"), color)
            self.gen_chip.configure(fg_color=bg)
            if self._mini_mode and hasattr(self, "mini_gen_dot"):
                self._set_mini_dot(self.mini_gen_dot, "loader", color)
        except Exception:
            pass
        self._gen_blink_job = self.after(450, self._gen_blink_tick)

    def _stop_gen_blink(self):
        if self._gen_blink_job:
            try: self.after_cancel(self._gen_blink_job)
            except Exception: pass
            self._gen_blink_job = None
        try: self.gen_chip.configure(fg_color=C_CARD)
        except Exception: pass

    def _set_fname_caption(self, path):
        """プレビュー下のファイル名キャプションを更新"""
        if not hasattr(self, "fname_cap"):
            return
        if not path or not os.path.exists(path) or self._mini_mode or self._preview_hidden:
            self.fname_cap.pack_forget(); return   # ミニ中は絵が主役／Hide中はファイル名も隠す
        nm = os.path.basename(path)
        try:
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y/%m/%d %H:%M")
        except Exception:
            ts = ""
        self.fname_cap_name.configure(text=nm)
        self.fname_cap_date.configure(text=(f"·  {ts}" if ts else ""))
        self.fname_cap.pack(pady=(10, 0))

    def _show_tip(self, widget, text):
        self._hide_tip()
        try:
            x = widget.winfo_rootx() + 6
            y = widget.winfo_rooty() - 26
            tip = tk.Toplevel(self); tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}"); tip.attributes("-topmost", True)
            tk.Label(tip, text=text, bg="#3a343f", fg="white",
                font=("Consolas", 9), padx=8, pady=3).pack()
            self._tooltip = tip
        except Exception:
            pass

    def _hide_tip(self):
        if self._tooltip is not None:
            try: self._tooltip.destroy()
            except Exception: pass
            self._tooltip = None

    def _scroll_history(self, direction):
        """カルーセルの矢印：1クリックでサムネ1枚分"""
        try:
            canvas = self._history_row._parent_canvas
            canvas.configure(xscrollincrement=80)   # サムネ1枚分（72px＋余白8px）
            canvas.xview_scroll(direction, "units")
        except Exception:
            pass

    def _select_newest_history(self, path):
        """生成直後：ピンクの選択枠を最新サムネへ移し、カルーセルを先頭まで戻す"""
        self._history_selected = path
        try:
            self._history_row._parent_canvas.xview_moveto(0)
        except Exception:
            pass

    # ── ミニモード：ポラロイド風フィット ──
    def _mini_fit_size(self):
        """ミニ窓の幅いっぱい（細い白枠＋下のバー帯だけ広め）に絵をフィットさせるサイズ"""
        self.update_idletasks()
        w = max(self.winfo_width()  - 30, 120)
        h = max(self.winfo_height() - 78, 120)
        return (w, h)

    def _rescale_mini_preview(self):
        self._mini_resize_job = None
        if not self._mini_mode:
            return
        if self._preview_hidden:
            self._apply_hide_cover()
        elif self._last_img_bytes:
            self._show_preview(self._last_img_bytes)

    def _on_mini_configure(self, e=None):
        """ミニ中のリサイズに追従して絵を再フィット（デバウンス付き）"""
        if not self._mini_mode or (e is not None and e.widget is not self):
            return
        size = (self.winfo_width(), self.winfo_height())
        if size == self._mini_last_size:
            return
        self._mini_last_size = size
        if self._mini_resize_job:
            self.after_cancel(self._mini_resize_job)
        self._mini_resize_job = self.after(200, self._rescale_mini_preview)

    def _restore_preview_after_mini(self):
        if self._mini_mode:
            return
        if self._preview_hidden:
            self._apply_hide_cover()
        elif self._last_img_bytes:
            self._show_preview(self._last_img_bytes)

    def _set_lang(self, lang):
        if lang != self.lang:
            self._toggle_lang()

    def _box_write(self, box, text):
        """欄の内容をまるごと書き換える"""
        box.delete("1.0", "end")
        if text:
            box.insert("1.0", text)

    def _on_box_edited(self, which):
        """手入力を生成対象へ反映する（欄の内容＝いま生成に使われる内容）"""
        if which == "pos_box":
            self._strip_spice_display()
            text = self.pos_box.get("1.0", "end").strip()
            if text != self._positive:
                self._positive = text
                self._pos_source = "manual" if text else None
        else:
            text = self.neg_box.get("1.0", "end").strip()
            if text != self._negative:
                self._negative = text
                self._neg_source = "manual" if text else None
        self._update_recv_indicators(bool(self._positive), bool(self._negative))
        self._refresh_go_btn()

    def _strip_spice_display(self):
        """生成時に表示したスパイス追記（紫タグ）を欄から外してrawに戻す
        （残したまま編集→同期するとスパイスが二重掛けになるため）"""
        try:
            tb = self.pos_box._textbox
            ranges = tb.tag_ranges("spice_tag")
            if ranges:
                tb.delete(ranges[0], ranges[1])
                tb.tag_delete("spice_tag")
        except Exception:
            pass

    # ── UI構築 ──────────────────────────────────────
    def _build_ui(self):

        self.configure(fg_color=C_BG)

        # ── タイトルバー ──
        tbar = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=0, height=56)
        tbar.pack(fill="x"); tbar.pack_propagate(False)
        self._tbar = tbar
        self._hairline = ctk.CTkFrame(self, fg_color=C_BORDER, height=1)
        self._hairline.pack(fill="x")   # ヘアライン
        lt = ctk.CTkFrame(tbar, fg_color="transparent"); lt.pack(side="left", padx=16)
        _ti = ICON("sparkles", C_PINK, 22)
        ctk.CTkLabel(lt, text="" if _ti else "🎀", image=_ti).pack(side="left", padx=(0,8))
        ctk.CTkLabel(lt, text="ぷろんぷたん", font=("Yu Gothic UI",17,"bold"),
                     text_color=C_INK).pack(side="left")
        rt = ctk.CTkFrame(tbar, fg_color="transparent"); rt.pack(side="right", padx=14)
        # ⚙️設定（ギアアイコン）
        _gi = ICON("settings", C_SUB, 20)
        ctk.CTkButton(rt, text="" if _gi else "⚙", image=_gi, width=40, height=34,
            fg_color="transparent", hover_color=C_PINK_SOFT, text_color=C_SUB,
            corner_radius=10, command=self._open_settings_window).pack(side="right", padx=2)
        # 📌 Mini ピル
        _pi = ICON("pin", C_PINK, 16)
        self._mini_btn = ctk.CTkButton(rt, text="Mini", image=_pi, compound="left",
            width=78, height=34, font=("Yu Gothic UI",12,"bold"),
            fg_color=C_PINK_SOFT, hover_color=C_ACCENT_L, text_color=C_PINK,
            corner_radius=999, command=self._toggle_mini)
        self._mini_btn.pack(side="right", padx=6)

        # ── 本体 ──
        content = ctk.CTkFrame(self, fg_color=C_BG)
        content.pack(fill="both", expand=True)

        # 右パネル外枠（固定幅・生成ボタンはここに固定）
        right_outer = ctk.CTkFrame(content, fg_color=C_BG, width=420)
        right_outer.pack(side="right", fill="y", padx=(0,14), pady=14)
        right_outer.pack_propagate(False)
        self._right_outer = right_outer

        # 右パネル内（固定レイアウト・縦スクロールバー無し）
        right = ctk.CTkFrame(right_outer, fg_color=C_BG)
        right.pack(fill="both", expand=True)

        # 左パネル（プレビュー可変幅）
        left = ctk.CTkFrame(content, fg_color=C_CARD, corner_radius=16)
        left.pack(side="left", fill="both", expand=True, padx=(14,6), pady=14)
        self._left_panel = left  # L=fill用に参照保存

        # スパイスパネル（プレビューの上にオーバーレイ）
        self._spice_panel_frame = ctk.CTkFrame(left, fg_color=C_STATUS,
            corner_radius=12, width=240)
        self._spice_panel_frame.pack_propagate(False)
        self._build_spice_panel(self._spice_panel_frame)
        # 起動時に開く設定なら表示
        if self.config_data.get("spice_panel_open_on_start", False):
            self._spice_panel_frame.place(relx=1.0, rely=0.0, anchor="ne",
                relheight=1.0, x=-8, y=8)

        self._build_preview_panel(left)
        self._build_control_panel(right, right_outer)
        self._update_mode_status()
        self.after(300, self._refresh_history)
        if self._forge_synced:
            self.after(200, self._update_forge_display)
        # ミニ中のリサイズで絵を再フィット（常設バインド・ミニ以外では即return）
        self.bind("<Configure>", self._on_mini_configure, add="+")


    def _build_preview_panel(self, parent):

        # プレビュー（画像＋ファイル名キャプションを中央に）
        center = ctk.CTkFrame(parent, fg_color="transparent")
        center.pack(expand=True)
        self.preview_lbl = ctk.CTkLabel(
            center, text=self.S("preview_wait"),
            font=("Yu Gothic UI",12), text_color=C_FAINT, cursor="hand2")
        self.preview_lbl.pack()
        self.preview_lbl.bind("<Button-1>", self._on_preview_click)
        self._reg("preview_wait", lambda: (
            self.preview_lbl.configure(text=self.S("preview_wait"))
            if not hasattr(self, '_preview_image') or self._preview_image is None else None))
        # ファイル名＋日時キャプション（初期は非表示）
        self.fname_cap = ctk.CTkFrame(center, fg_color=C_STATUS, corner_radius=8)
        _fi = ICON("image", C_SUB, 13)
        ctk.CTkLabel(self.fname_cap, text="" if _fi else "🖼", image=_fi).pack(side="left", padx=(9,5), pady=5)
        self.fname_cap_name = ctk.CTkLabel(self.fname_cap, text="", font=("Consolas",10), text_color=C_INK)
        self.fname_cap_name.pack(side="left")
        self.fname_cap_date = ctk.CTkLabel(self.fname_cap, text="", font=("Yu Gothic UI",10), text_color=C_FAINT)
        self.fname_cap_date.pack(side="left", padx=(7,11))

        # ミニモード用バー（通常時は非表示。絵が主役＝極小ランプ＋控えめアイコンのみ）
        self._mini_lamp_bar = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        self._mini_lamp_bar.pack_propagate(False)
        def _mini_dot(letter):
            f = ctk.CTkFrame(self._mini_lamp_bar, fg_color="transparent")
            _di = ICON("circle", C_FAINT, 11)
            d = ctk.CTkLabel(f, text="" if _di else "●", image=_di,
                font=("Yu Gothic UI", 9), text_color=C_FAINT)
            d.pack(side="left")
            l = ctk.CTkLabel(f, text=letter, font=("Yu Gothic UI", 9), text_color=C_FAINT)
            l.pack(side="left", padx=(3, 0))
            f._dot, f._lbl = d, l
            return f
        self.mini_pos_dot = _mini_dot("P");   self.mini_pos_dot.pack(side="left", padx=(10, 4))
        self.mini_neg_dot = _mini_dot("N");   self.mini_neg_dot.pack(side="left", padx=4)
        self.mini_gen_dot = _mini_dot("GEN"); self.mini_gen_dot.pack(side="left", padx=4)
        _ri2 = ICON("maximize-2", C_SUB, 14)
        ctk.CTkButton(self._mini_lamp_bar, text="" if _ri2 else "□", image=_ri2,
            width=28, height=24, fg_color="transparent", hover_color=C_PINK_SOFT,
            text_color=C_SUB, corner_radius=8,
            command=self._toggle_mini).pack(side="right", padx=(2, 8))
        _hi2 = ICON("eye-off", C_SUB, 14)
        ctk.CTkButton(self._mini_lamp_bar, text="" if _hi2 else "H", image=_hi2,
            width=28, height=24, fg_color="transparent", hover_color=C_PINK_SOFT,
            text_color=C_SUB, corner_radius=8,
            command=lambda: self._set_preview_size("Hide", "hide")).pack(side="right", padx=2)

        # サイズ・セグメント
        sz_outer = ctk.CTkFrame(parent, fg_color="transparent")
        sz_outer.pack(pady=(2,2))
        self._sz_frame = sz_outer
        seg = ctk.CTkFrame(sz_outer, fg_color=C_STATUS, corner_radius=10)
        seg.pack()
        self._sz_btns = {}
        for sz, key, si in [("S","prev_s",(140,140)),("M","prev_m",(280,340)),
                              ("L","prev_l",None),("Hide","prev_hide","hide")]:
            _sz, _k, _si = sz, key, si
            active = sz == "M"
            b = ctk.CTkButton(seg, text=self.S(key), width=46, height=28,
                               font=("Yu Gothic UI",11,"bold"), corner_radius=8,
                               fg_color=C_PINK if active else "transparent",
                               hover_color=C_PINK_SOFT,
                               text_color="white" if active else C_SUB,
                               command=lambda s=_sz, i=_si: self._set_preview_size(s, i))
            b.pack(side="left", padx=3, pady=3)
            self._sz_btns[sz] = b
            self._reg(f"sz_{sz}", lambda k=_k, btn=b: btn.configure(text=self.S(k)))

        # 生成履歴（カルーセル）
        self._build_history_strip(parent)

        # ボトムバー（アイコン付き）
        bot = ctk.CTkFrame(parent, fg_color="transparent")
        bot.pack(fill="x", padx=14, pady=(6,14))
        self._bot_bar = bot
        def _botbtn(icon_name, key, cmd, disabled=False):
            b = ctk.CTkButton(bot, text=self.S(key), image=ICON(icon_name, C_SUB, 16), compound="left",
                height=34, font=("Yu Gothic UI",11), fg_color=C_STATUS, hover_color=C_PINK_SOFT,
                text_color=C_SUB, corner_radius=10,
                state="disabled" if disabled else "normal", command=cmd)
            b.pack(side="left", expand=True, fill="x", padx=3)
            return b
        self.open_file_btn = _botbtn("image", "open_file", self._open_image_file, disabled=True)
        self._reg("open_file", lambda: self.open_file_btn.configure(text=self.S("open_file")))
        self.open_folder_btn = _botbtn("folder", "open_folder", self._open_save_folder, disabled=True)
        self._reg("open_folder", lambda: self.open_folder_btn.configure(text=self.S("open_folder")))
        self.manual_btn_w = _botbtn("book-open", "open_manual", self._open_manual)
        self._reg("open_manual", lambda: self.manual_btn_w.configure(text=self.S("open_manual")))
        self.rules_btn = ctk.CTkButton(bot, text="お約束", image=ICON("scroll-text","white",16),
            compound="left", height=34, font=("Yu Gothic UI",11,"bold"),
            fg_color=C_PINK, hover_color=C_PINK_H, text_color="white", corner_radius=10,
            command=self._copy_rules)
        self.rules_btn.pack(side="left", expand=True, fill="x", padx=3)


    # ── 生成履歴カルーセル ─────────────────────────────
    def _build_history_strip(self, parent):
        """最近生成した画像をカルーセル表示（‹›矢印＋チラ見せ＋ハイブリッドバー）"""
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", pady=(0,2))
        self._history_strip = wrap

        hdr = ctk.CTkFrame(wrap, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(0,2))
        _hi = ICON("heart", C_PINK, 15)
        ctk.CTkLabel(hdr, text="" if _hi else "♡", image=_hi).pack(side="left", padx=(0,5))
        self.history_lbl = ctk.CTkLabel(hdr, text=self.S("history_lbl"),
            font=("Yu Gothic UI",12,"bold"), text_color=C_INK)
        self.history_lbl.pack(side="left")
        self._reg("history_lbl", lambda: self.history_lbl.configure(text=self.S("history_lbl")))
        _ri = ICON("refresh-cw", C_SUB, 16)
        ctk.CTkButton(hdr, text="" if _ri else "↻", image=_ri, width=28, height=24,
            fg_color="transparent", hover_color=C_PINK_SOFT, text_color=C_SUB,
            corner_radius=8, command=self._refresh_history).pack(side="right")

        # カルーセル本体： ‹ [横スクロール枠] ›
        caro = ctk.CTkFrame(wrap, fg_color="transparent")
        caro.pack(fill="x", padx=10)
        _cl = ICON("chevron-left", C_SUB, 18)
        ctk.CTkButton(caro, text="" if _cl else "‹", image=_cl, width=26, height=88,
            fg_color="transparent", hover_color=C_PINK_SOFT, corner_radius=8,
            command=lambda: self._scroll_history(-1)).pack(side="left")
        _cr = ICON("chevron-right", C_PINK, 18)
        ctk.CTkButton(caro, text="" if _cr else "›", image=_cr, width=26, height=88,
            fg_color="transparent", hover_color=C_PINK_SOFT, corner_radius=8,
            command=lambda: self._scroll_history(1)).pack(side="right")
        # 横スクロール枠（バーは地色に溶けて普段ほぼ見えず、ホバーで濃く＝ハイブリッド）
        self._history_row = ctk.CTkScrollableFrame(
            caro, fg_color=C_STATUS, orientation="horizontal", height=88,
            scrollbar_button_color=C_STATUS, scrollbar_button_hover_color=C_ACCENT,
            corner_radius=12)
        self._history_row.pack(side="left", fill="x", expand=True, padx=2)


    def _refresh_history(self):
        """保存フォルダをスキャンしてサムネ更新（重い処理は別スレッド）"""
        save_dir = self.config_data.get("save_dir", "")
        threading.Thread(target=self._scan_history, args=(save_dir,), daemon=True).start()


    def _scan_history(self, save_dir):
        files = []
        if save_dir and os.path.isdir(save_dir):
            try:
                files = [os.path.join(save_dir, f) for f in os.listdir(save_dir)
                         if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
                files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            except Exception:
                files = []
        files = files[:12]
        thumbs = []
        for path in files:
            try:
                pil = Image.open(path).convert("RGB")
                pil.thumbnail((64, 64), Image.LANCZOS)
                thumbs.append((path, pil))
            except Exception:
                continue
        self.after(0, self._populate_history, thumbs)


    def _populate_history(self, thumbs):
        if not hasattr(self, "_history_row") or not self._history_row.winfo_exists():
            return
        for w in self._history_row.winfo_children():
            w.destroy()
        self._history_imgs = []
        self._history_btns = {}
        if self._preview_hidden:          # Hide中はサムネも出さない（プライバシー）
            ctk.CTkLabel(self._history_row, text=self.S("history_hidden"),
                font=("Yu Gothic UI", 11, "bold"), text_color=C_SUB).pack(
                side="left", padx=14, pady=10)
            return
        if not thumbs:
            ctk.CTkLabel(self._history_row, text=self.S("history_empty"),
                font=("Yu Gothic UI", 11), text_color=C_SUB, justify="left").pack(
                side="left", padx=12, pady=10)
            return
        for path, pil in thumbs:
            img = ctk.CTkImage(light_image=pil, size=(pil.width, pil.height))
            self._history_imgs.append(img)
            sel = (path == self._history_selected)
            b = ctk.CTkButton(self._history_row, text="", image=img,
                width=72, height=72, fg_color=C_CARD, hover_color=C_PINK_SOFT,
                border_width=3 if sel else 2, border_color=C_PINK if sel else C_BORDER,
                corner_radius=10, command=lambda p=path: self._on_history_click(p))
            b.pack(side="left", padx=4, pady=8)
            self._history_btns[path] = b
            nm = os.path.basename(path)
            b.bind("<Enter>", lambda e, w=b, t=nm: self._show_tip(w, t))
            b.bind("<Leave>", lambda e: self._hide_tip())


    def _on_history_click(self, path):
        """履歴サムネをクリック → 大プレビューに表示して操作対象にする"""
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            return
        self._last_saved_path = path
        self._preview_hidden = False
        self._history_selected = path
        # 選択枠ハイライト更新
        for p, b in self._history_btns.items():
            s = (p == path)
            try:
                b.configure(border_width=3 if s else 2,
                            border_color=C_PINK if s else C_BORDER)
            except Exception:
                pass
        self._show_preview(data)
        self._set_fname_caption(path)
        self.open_file_btn.configure(state="normal")
        self.open_folder_btn.configure(state="normal")
        self._set_status(self.S("st_history_view"), C_ACCENT)
        self._hide_tip()


    def _build_control_panel(self, parent, outer=None):

        # ── ステータスカード ──
        sc = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=14,
            border_width=1, border_color=C_BORDER)
        sc.pack(fill="x", pady=(0,12))
        sc_top = ctk.CTkFrame(sc, fg_color="transparent")
        sc_top.pack(fill="x", padx=14, pady=(10,4))
        self.sd_chip = self._chip(sc_top, "circle", self.S("chip_sd_off"), C_RED)
        self.sd_chip.pack(side="left")
        self.mode_chip = self._chip(sc_top, "zap", self.S("sb_mode_auto").split(" ",1)[-1], C_ORANGE)
        self.mode_chip.pack(side="left", padx=6)
        self.gen_chip = self._chip(sc_top, "loader", self.S("chip_busy"), C_ORANGE)  # 生成中のみpack
        self.port_lbl = ctk.CTkLabel(sc_top, text=self.S("sb_starting"),
            font=("Yu Gothic UI",10), text_color=C_FAINT)
        self.port_lbl.pack(side="right")
        self._reg("port_lbl", lambda: self.port_lbl.configure(
            text=self.S("sb_port", p=self._port_num)
            if self._port_num != PORT_RANGE_START else self.S("sb_starting")))
        self._reg("sb_mode", lambda: self._update_mode_status())

        self.status_lbl = ctk.CTkLabel(sc, text=self.S("st_waiting"),
            font=("Yu Gothic UI",14,"bold"), text_color=C_INK, justify="left")
        self.status_lbl.pack(anchor="w", padx=14, pady=(0,2))

        ts_row = ctk.CTkFrame(sc, fg_color="transparent")
        ts_row.pack(fill="x", padx=14, pady=(0,6))
        self.ts_pos_lbl = ctk.CTkLabel(ts_row, text="", font=("Yu Gothic UI",9), text_color=C_FAINT)
        self.ts_pos_lbl.pack(side="left")
        self.ts_neg_lbl = ctk.CTkLabel(ts_row, text="", font=("Yu Gothic UI",9), text_color=C_FAINT)
        self.ts_neg_lbl.pack(side="left", padx=(10,0))
        self.ts_gen_lbl = ctk.CTkLabel(ts_row, text="", font=("Yu Gothic UI",9,"bold"), text_color=C_GREEN)
        self.ts_gen_lbl.pack(side="right")

        # ── ポジ/ネガ 入力欄 ──
        def _field(label_key, copy_box_attr, accent, h):
            head = ctk.CTkFrame(parent, fg_color="transparent")
            head.pack(fill="x", pady=(0,3))
            lbl = ctk.CTkLabel(head, text=self.S(label_key),
                font=("Yu Gothic UI",13,"bold"), text_color=C_INK)
            lbl.pack(side="left")
            self._reg(label_key, lambda l=lbl, k=label_key: l.configure(text=self.S(k)))
            pill = self._chip(head, "circle", self.S("pill_wait"), C_SUB)
            pill.pack(side="left", padx=8)
            _xi = ICON("x", C_FAINT, 15)
            ctk.CTkButton(head, text="" if _xi else "✕", image=_xi, width=30, height=26,
                fg_color="transparent", hover_color=C_PINK_SOFT, corner_radius=8,
                command=(self._clear_pos if copy_box_attr=="pos_box" else self._clear_neg)
                ).pack(side="right")
            _ci = ICON("copy", C_SUB, 15)
            cpy = ctk.CTkButton(head, text="" if _ci else "📋", image=_ci, width=30, height=26,
                fg_color="transparent", hover_color=C_PINK_SOFT, corner_radius=8,
                command=lambda: self._copy_text(getattr(self, copy_box_attr)))
            cpy.pack(side="right", padx=(0,2))
            box = ctk.CTkTextbox(parent, height=h, font=("Consolas",11),
                fg_color=C_CARD, border_width=1, border_color=C_BORDER, corner_radius=10)
            box.pack(fill="x", pady=(0,6))
            # 手入力OK：編集内容がそのまま生成対象に同期される
            try:
                box._textbox.bind("<KeyRelease>",
                    lambda e, a=copy_box_attr: self._on_box_edited(a), add="+")
                if copy_box_attr == "pos_box":
                    # スパイス紫表示が残ったまま編集に入らないように剥がす
                    box._textbox.bind("<FocusIn>",
                        lambda e: self._strip_spice_display(), add="+")
            except Exception:
                pass
            return lbl, pill, cpy, box

        self.pos_lbl, self.pos_status, self.pos_cpy_btn, self.pos_box = _field("lbl_pos","pos_box",C_GREEN,60)
        self.neg_lbl, self.neg_status, self.neg_cpy_btn, self.neg_box = _field("lbl_neg","neg_box",C_RED,44)

        # ── スパイス ＋ ネガ補強 ──
        for i in range(1, 10):
            self._spice_checks[i] = ctk.BooleanVar(value=False)
        self._spice_focused_idx = None
        sr = ctk.CTkFrame(parent, fg_color="transparent")
        sr.pack(fill="x", pady=(2,8))
        self.spice_open_btn = ctk.CTkButton(sr, text="スパイス",
            image=ICON("sparkles", C_ACCENT, 16), compound="left",
            height=36, font=("Yu Gothic UI",12,"bold"),
            fg_color=C_PURPLE_S, hover_color=C_ACCENT_L, text_color=C_ACCENT,
            corner_radius=10, command=self._toggle_spice_panel)
        self.spice_open_btn.pack(side="left")
        nb = ctk.CTkFrame(sr, fg_color="transparent"); nb.pack(side="right")
        ctk.CTkLabel(nb, text="", image=ICON("shield-check", C_SUB, 16)).pack(side="left", padx=(0,5))
        nb_lbl = ctk.CTkLabel(nb, text=self.S("neg_boost_btn"), font=("Yu Gothic UI",10), text_color=C_SUB)
        nb_lbl.pack(side="left", padx=(0,8))
        self._reg("neg_boost_btn", lambda: nb_lbl.configure(text=self.S("neg_boost_btn")))
        self.neg_boost_switch = ctk.CTkSwitch(nb, text="", variable=self._neg_boost_on,
            width=42, progress_color=C_PINK, button_color="white")
        self.neg_boost_switch.pack(side="left")

        # ── モード ＋ クオリティ（選択行）──
        mq = ctk.CTkFrame(parent, fg_color="transparent")
        mq.pack(fill="x", pady=(0,8))
        def _split_title(k):
            s = self.S(k).split("\n")
            t = s[0].split(" ",1)[-1] if " " in s[0] else s[0]
            return t, (s[1] if len(s) > 1 else "")
        def _reg_row(row, key):
            def upd():
                t, sub = _split_title(key)
                row._tl.configure(text=t)
                if row._sl and sub: row._sl.configure(text=sub)
            return upd

        # モード
        mode_card = ctk.CTkFrame(mq, fg_color=C_CARD, corner_radius=12, border_width=1, border_color=C_BORDER)
        mode_card.pack(side="left", fill="both", expand=True, padx=(0,6))
        ml = ctk.CTkLabel(mode_card, text=self.S("mode_lbl"), font=("Yu Gothic UI",10,"bold"), text_color=C_SUB)
        ml.pack(anchor="w", padx=12, pady=(8,2))
        self._reg("mode_lbl", lambda: ml.configure(text=self.S("mode_lbl")))
        self.mode_var = ctk.StringVar(value="auto")
        t,sub = _split_title("mode_auto")
        ra = self._select_row(mode_card,"auto","zap",t,sub,self.mode_var,self._enable_auto)
        ra.pack(fill="x", padx=8, pady=2)
        self._reg("mode_auto", _reg_row(ra,"mode_auto"))
        t,sub = _split_title("mode_manual")
        rm = self._select_row(mode_card,"manual","eye",t,sub,self.mode_var,self._enable_manual)
        rm.pack(fill="x", padx=8, pady=(2,8))
        self._reg("mode_manual", _reg_row(rm,"mode_manual"))
        self._refresh_select_group(mode_card, self.mode_var)

        # クオリティ
        qual_card = ctk.CTkFrame(mq, fg_color=C_CARD, corner_radius=12, border_width=1, border_color=C_BORDER)
        qual_card.pack(side="left", fill="both", expand=True, padx=(6,0))
        ql = ctk.CTkLabel(qual_card, text=self.S("quality_lbl"), font=("Yu Gothic UI",10,"bold"), text_color=C_SUB)
        ql.pack(anchor="w", padx=12, pady=(8,2))
        self._reg("quality_lbl", lambda: ql.configure(text=self.S("quality_lbl")))
        self.preset_var = ctk.StringVar(value="normal")
        for val, key, icon_n, steps, sampler in [
            ("fast",  "preset_fast",  "zap",      "12","Euler a"),
            ("normal","preset_normal","sparkles", "28","DPM++ 2M Karras"),
            ("hq",    "preset_hq",    "gem",      "45","DPM++ 2M Karras"),
        ]:
            _s,_sa = steps,sampler
            t,_ = _split_title(key)
            rr = self._select_row(qual_card,val,icon_n,t,"",self.preset_var,
                lambda s=_s,sa=_sa: self._apply_preset(s,sa))
            rr.pack(fill="x", padx=8, pady=1)
            self._reg(f"preset_{val}", _reg_row(rr,key))
        t,_ = _split_title("preset_forge")
        rf = self._select_row(qual_card,"forge_sync","refresh-cw",t,"",self.preset_var,self._apply_forge_preset)
        rf.pack(fill="x", padx=8, pady=(1,0))
        self._reg("preset_forge", _reg_row(rf,"preset_forge"))
        self.forge_info_lbl = ctk.CTkLabel(qual_card, text=self.S("forge_no_sync"),
            font=("Yu Gothic UI",8), text_color=C_FAINT)
        self.forge_info_lbl.pack(anchor="w", padx=(40,10), pady=(0,8))
        self._refresh_select_group(qual_card, self.preset_var)

        # ── 生成ボタン（スクロール外に固定）──
        _outer = outer if outer is not None else parent
        self.go_btn = ctk.CTkButton(
            _outer, text=self.S("go_waiting"), image=ICON("wand-sparkles", C_FAINT, 20), compound="left",
            height=54, font=("Yu Gothic UI",15,"bold"), fg_color="#e6deea", hover_color="#ddd2e4",
            text_color=C_FAINT, corner_radius=12, command=self._on_go_btn, state="disabled")
        self.go_btn.pack(fill="x", side="bottom", pady=(4,2), padx=0)


    def _toggle_spice(self, idx):
        """スパイスON/OFF切り替え"""
        var = self._spice_checks.get(idx)
        if not var:
            return
        var.set(not var.get())
        self._refresh_spice_row_color(idx)

    def _refresh_spice_row_color(self, idx):
        """スパイス行の色をON/OFFに応じて更新"""
        row = self._spice_rows.get(idx)
        num_btn = self._spice_btns.get(idx)
        lbl = self._spice_row_lbls.get(idx)
        if not row or not num_btn:
            return
        is_on = self._spice_checks.get(idx, ctk.BooleanVar()).get()
        if is_on:
            row.configure(fg_color=C_LAVENDER)
            num_btn.configure(fg_color=C_ACCENT, text_color="white")
            if lbl: lbl.configure(text_color=C_PURPLE)
        else:
            row.configure(fg_color="transparent")
            num_btn.configure(fg_color=C_BORDER, text_color=C_TEXT_S)
            if lbl: lbl.configure(text_color=C_TEXT_S)

    def _build_spice_panel(self, parent):
        """スパイスパネルの中身を構築"""
        # ヘッダー
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(10,4))
        _spi = ICON("sparkles", C_ACCENT, 14)
        if _spi:
            ctk.CTkLabel(hdr, text="", image=_spi).pack(side="left", padx=(0,5))
        ctk.CTkLabel(hdr, text="ポジスパイス",
            font=("",11,"bold"), text_color=C_PURPLE).pack(side="left")
        ctk.CTkButton(hdr, text="✕", width=26, height=22,
            font=("",11), fg_color="transparent", hover_color=C_BORDER,
            text_color=C_TEXT_S, corner_radius=6,
            command=self._toggle_spice_panel).pack(side="right")

        # 起動時に開くチェック
        boot_row = ctk.CTkFrame(parent, fg_color="transparent")
        boot_row.pack(fill="x", padx=10, pady=(0,6))
        ctk.CTkLabel(boot_row, text="起動時に開く",
            font=("",10), text_color=C_TEXT_S).pack(side="left")
        ctk.CTkCheckBox(boot_row, text="", variable=self._spice_panel_open,
            width=24, checkbox_width=16, checkbox_height=16,
            fg_color=C_ACCENT, hover_color=C_ACCENT_L,
            command=self._save_spice_panel_pref).pack(side="right")

        # 区切り線
        ctk.CTkFrame(parent, fg_color=C_BORDER, height=1).pack(fill="x", padx=10, pady=(0,6))

        # スパイスリスト
        self._spice_rows = {}
        self._spice_row_lbls = {}
        for i in range(1, 10):
            _i = i
            row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=6)
            row.pack(fill="x", padx=8, pady=2)
            self._spice_rows[i] = row

            num_btn = ctk.CTkButton(
                row, text=str(i), width=26, height=26,
                font=("",10,"bold"), corner_radius=13,
                fg_color=C_BORDER, hover_color=C_ACCENT_L,
                text_color=C_TEXT_S,
                command=lambda idx=_i: self._toggle_spice(idx))
            num_btn.pack(side="left", padx=(6,6), pady=4)
            self._spice_btns[i] = num_btn

            text_val = self.config_data.get(f"spice_{i}", "")
            entry = ctk.CTkEntry(row, font=("",10), height=24,
                fg_color="transparent", border_width=0,
                text_color=C_TEXT_S,
                placeholder_text=f"スパイス {i}")
            entry.insert(0, text_val)

            # undo履歴
            _history = [text_val]
            _hist_pos = [0]
            def _on_key(e, en=entry, h=_history, hp=_hist_pos):
                if e.keysym in ("z","Z") and (e.state & 0x4):
                    return  # Ctrl+Zはundoハンドラで処理
                cur = en.get()
                if not h or h[hp[0]] != cur:
                    del h[hp[0]+1:]
                    h.append(cur)
                    hp[0] = len(h)-1
            def _on_undo(e, en=entry, h=_history, hp=_hist_pos):
                if hp[0] > 0:
                    hp[0] -= 1
                    val = h[hp[0]]
                    en.delete(0, "end")
                    en.insert(0, val)
                return "break"
            entry._entry.bind("<Key>", _on_key)
            entry._entry.bind("<Control-z>", _on_undo)
            entry._entry.bind("<Control-Z>", _on_undo)

            entry.pack(side="left", fill="x", expand=True, padx=(0,6), pady=4)
            self._spice_entries[i] = entry
            self._spice_row_lbls[i] = entry
            entry.bind("<FocusOut>", lambda e, idx=_i: self._save_spice_entry(idx))
            entry.bind("<Return>",   lambda e, idx=_i: self._save_spice_entry(idx))

            # 初期色
            self._refresh_spice_row_color(i)

    def _save_spice_entry(self, idx):
        """エントリの内容を即時保存"""
        entry = self._spice_entries.get(idx)
        if entry:
            self.config_data[f"spice_{idx}"] = entry.get().strip()
            self._save_config()

    def _save_spice_panel_pref(self):
        """起動時に開く設定を保存"""
        self.config_data["spice_panel_open_on_start"] = self._spice_panel_open.get()
        self._save_config()

    def _toggle_spice_panel(self):
        """スパイスパネルの開閉"""
        if self._spice_panel_frame.winfo_ismapped():
            self._spice_panel_frame.place_forget()
            self.spice_open_btn.configure(text="スパイス ▶")
        else:
            self._spice_panel_frame.place(relx=1.0, rely=0.0, anchor="ne",
                relheight=1.0, x=-8, y=8)
            self.spice_open_btn.configure(text="スパイス ◀")


    def _open_settings_window(self):
        """設定ウィンドウをモーダルで開く"""
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return

        win = ctk.CTkToplevel(self)
        win.title("⚙️  設定")
        win.geometry("500x660")
        self._settings_win = win
        win.configure(fg_color=C_BG)
        # 親が最前面でも確実に手前に出す
        win.transient(self)
        win.grab_set()
        win.lift()
        win.attributes("-topmost", True)
        win.after(400, lambda: win.winfo_exists() and win.attributes("-topmost", False))
        win.after(60, win.focus_force)

        scroll = ctk.CTkScrollableFrame(win, fg_color=C_BG,
            scrollbar_button_color=C_ACCENT_L,
            scrollbar_button_hover_color=C_ACCENT)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        self.setting_entries = {}

        def section(text):
            ctk.CTkLabel(scroll, text=text, font=("",12,"bold"),
                text_color=C_ACCENT).pack(pady=(14,4), anchor="w")

        def labeled_entry(label_text, key, default=""):
            ctk.CTkLabel(scroll, text=label_text, font=("",11),
                text_color=C_TEXT).pack(anchor="w", pady=(4,1))
            e = ctk.CTkEntry(scroll, font=("",12), border_color=C_BORDER)
            e.insert(0, self.config_data.get(key, default))
            e.pack(fill="x", pady=(0,2))
            self.setting_entries[key] = e

        # 言語 / Language
        section(self.S("s_lang_title"))
        self._lang_seg = ctk.CTkSegmentedButton(scroll,
            values=[self.S("s_lang_ja"), self.S("s_lang_en")],
            selected_color=C_PINK, selected_hover_color=C_PINK_H,
            unselected_color=C_STATUS, unselected_hover_color=C_ACCENT_L,
            fg_color=C_STATUS, text_color=C_INK,
            command=lambda v: self._set_lang("ja" if v == self.S("s_lang_ja") else "en"))
        self._lang_seg.set(self.S("s_lang_ja") if self.lang == "ja" else self.S("s_lang_en"))
        self._lang_seg.pack(fill="x", pady=(0,2))

        # SD接続
        section(self.S("s_sd_title"))
        labeled_entry(self.S("s_sd_url"), "sd_url")

        # Forge
        section(self.S("s_forge_title"))
        self.forge_import_btn = ctk.CTkButton(
            scroll, text=self.S("s_forge_btn"), height=32,
            font=("",11), fg_color=C_ACCENT_L, hover_color=C_ACCENT,
            text_color="white", corner_radius=8,
            command=self._import_forge_settings)
        self.forge_import_btn.pack(fill="x", pady=4)
        self._reg("s_forge_btn", lambda: self.forge_import_btn.configure(
            text=self.S("s_forge_btn")))
        self.forge_result_lbl = ctk.CTkLabel(scroll, text="", font=("",11))
        self.forge_result_lbl.pack(anchor="w")

        # 保存先
        section(self.S("s_save_title"))
        ctk.CTkLabel(scroll, text=self.S("s_save_dir"), font=("",11),
            text_color=C_TEXT).pack(anchor="w", pady=(4,1))
        ff = ctk.CTkFrame(scroll, fg_color="transparent")
        ff.pack(fill="x", pady=2)
        self.save_entry = ctk.CTkEntry(ff, font=("",12), border_color=C_BORDER)
        self.save_entry.insert(0, self.config_data.get("save_dir",""))
        self.save_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        self.browse_btn_w = ctk.CTkButton(ff, text=self.S("s_browse"), width=90, height=30,
            fg_color=C_ACCENT_L, hover_color=C_ACCENT, text_color="white",
            corner_radius=8, command=self._browse)
        self.browse_btn_w.pack(side="left")
        self._reg("s_browse", lambda: self.browse_btn_w.configure(text=self.S("s_browse")))
        self.setting_entries["save_dir"] = self.save_entry

        # パラメーター
        section(self.S("s_params_title"))
        pf = ctk.CTkFrame(scroll, fg_color=C_STATUS, corner_radius=10)
        pf.pack(fill="x", pady=4)
        for lk, ck in [("s_cfg","cfg"),("s_width","width"),("s_height","height")]:
            col = ctk.CTkFrame(pf, fg_color="transparent")
            col.pack(side="left", expand=True, padx=10, pady=10)
            ctk.CTkLabel(col, text=self.S(lk), font=("",11), text_color=C_TEXT).pack()
            e = ctk.CTkEntry(col, width=80, font=("",12), border_color=C_BORDER)
            e.insert(0, self.config_data.get(ck,""))
            e.pack()
            self.setting_entries[ck] = e

        # マーカー
        section(self.S("s_anchor_title"))
        note = ctk.CTkLabel(scroll, text=self.S("s_anchor_note"),
            font=("",10), text_color=C_TEXT_S)
        note.pack(anchor="w")
        self._reg("s_anchor_note", lambda: note.configure(text=self.S("s_anchor_note")))
        labeled_entry(self.S("s_pos_anchor"), "positive_anchor")
        labeled_entry(self.S("s_neg_anchor"), "negative_anchor")

        # スパイス内容
        section(self.S("s_spice_title"))
        sn = ctk.CTkLabel(scroll, text=self.S("s_spice_note"), font=("",10), text_color=C_TEXT_S)
        sn.pack(anchor="w")
        self._reg("s_spice_note", lambda: sn.configure(text=self.S("s_spice_note")))
        for i in range(1, 10):
            sf = ctk.CTkFrame(scroll, fg_color="transparent")
            sf.pack(fill="x", pady=2)
            ctk.CTkLabel(sf, text=f"{i}.", width=22, font=("",11,"bold"),
                text_color=C_ACCENT).pack(side="left")
            e = ctk.CTkEntry(sf, font=("",11), border_color=C_BORDER)
            e.insert(0, self.config_data.get(f"spice_{i}", ""))
            e.pack(side="left", fill="x", expand=True, padx=(6,0))
            self.setting_entries[f"spice_{i}"] = e
            self._spice_entries[i] = e

        # ネガ補強
        section(self.S("s_neg_title"))
        self.neg_boost_textbox = ctk.CTkTextbox(scroll, height=60, font=("Consolas",10),
            border_color=C_BORDER, border_width=1, corner_radius=8)
        self.neg_boost_textbox.insert("1.0", self.config_data.get("neg_boost",""))
        self.neg_boost_textbox.pack(fill="x", pady=4)

        # 保存ボタン
        self.save_btn_w = ctk.CTkButton(
            scroll, text=self.S("s_save_btn"), height=40,
            font=("",13), fg_color=C_GO, hover_color=C_GO_H,
            text_color="white", corner_radius=10, command=self._save_settings)
        self.save_btn_w.pack(pady=(16,4), fill="x")
        self._reg("s_save_btn", lambda: self.save_btn_w.configure(text=self.S("s_save_btn")))
        self.save_result_lbl = ctk.CTkLabel(scroll, text="", font=("",11))
        self.save_result_lbl.pack(pady=(0,20))
    # ── ロジック ─────────────────────────────────────
    def _apply_preset(self, steps, sampler):

        self.config_data["steps"]   = steps
        self.config_data["sampler"] = sampler


    def _apply_forge_preset(self):

        if not self._forge_synced:
            return
        for k in ("steps","cfg","width","height","sampler"):
            fv = self.config_data.get(f"forge_{k}","")
            if fv:
                self.config_data[k] = fv


    def _import_forge_settings(self):

        """Forgeから設定を取り込む（settings APIは使えないのでforge_sync.jsが送ってきた値を使用）"""
        url = self.config_data.get("sd_url","http://127.0.0.1:7860")
        def _try():

            try:
                r = requests.get(f"{url}/sdapi/v1/samplers", timeout=3)
                if r.status_code == 200:
                    self._sd_connected = True
                    self.after(0, self._update_sd_status)
                    self.after(0, lambda: self.forge_result_lbl.configure(
                        text=self.S("s_forge_ok"), text_color=C_GREEN))
                    self.after(0, lambda: self.after(
                        3000, lambda: self.forge_result_lbl.configure(text="")))
                else:
                    raise Exception()
            except:
                self.after(0, lambda: self.forge_result_lbl.configure(
                    text=self.S("s_forge_fail"), text_color=C_RED))
                self.after(0, lambda: self.after(
                    3000, lambda: self.forge_result_lbl.configure(text="")))
        threading.Thread(target=_try, daemon=True).start()


    def _update_sd_status(self):

        if hasattr(self, 'sd_chip'):
            if self._sd_connected:
                self._set_chip(self.sd_chip, "circle-check", self.S("chip_sd_on"), C_GREEN)
            else:
                self._set_chip(self.sd_chip, "circle", self.S("chip_sd_off"), C_RED)


    def _update_forge_display(self):

        if self._forge_synced:
            s = self.config_data.get("forge_steps","")
            c = self.config_data.get("forge_cfg","")
            w = self.config_data.get("forge_width","")
            h = self.config_data.get("forge_height","")
            if s and hasattr(self, 'forge_info_lbl'):
                self.forge_info_lbl.configure(
                    text=f"steps={s} CFG={c} {w}×{h}", text_color=C_ACCENT)
        elif hasattr(self, 'forge_info_lbl'):
            self.forge_info_lbl.configure(text=self.S("forge_no_sync"), text_color=C_FAINT)


    def _update_mode_status(self):

        if hasattr(self, 'mode_chip'):
            if self._auto_generate:
                self._set_chip(self.mode_chip, "zap",
                    self.S("sb_mode_auto").split(" ",1)[-1], C_ORANGE)
            else:
                self._set_chip(self.mode_chip, "eye",
                    self.S("sb_mode_manual").split(" ",1)[-1], "#3b82c4")


    def _update_recv_indicators(self, pos_ok, neg_ok):

        # 新着受信（seqが進んだ）ならミニランプをペカーっとさせる合図
        new_arrival = self._prompt_seq != self._prev_flash_seq
        self._prev_flash_seq = self._prompt_seq
        pos_flash = pos_ok and new_arrival
        neg_flash = neg_ok and new_arrival

        def _pill(ok, src):
            if not ok:
                return self.S("pill_wait")
            if src == "used":
                return self.S("pill_used")
            return self.S("pill_manual") if src == "manual" else self.S("pill_recv")
        def _col(ok, src, on_color):
            if not ok:
                return C_SUB
            return C_ACCENT if src == "used" else on_color   # 生成済みは紫＝ひと仕事終えた感
        if hasattr(self, 'pos_status'):
            self._set_chip(self.pos_status,
                "circle-check" if pos_ok else "circle",
                _pill(pos_ok, self._pos_source),
                _col(pos_ok, self._pos_source, C_GREEN))
        if hasattr(self, 'neg_status'):
            self._set_chip(self.neg_status,
                "circle-check" if neg_ok else "circle",
                _pill(neg_ok, self._neg_source),
                _col(neg_ok, self._neg_source, C_RED))
        # ミニランプ：点きっぱなし防止＝生成済みは薄チェックでお休み（ランプは「いま動きがあるか」担当）
        def _mini_state(ok, src, on_color):
            if not ok:
                return "circle", C_FAINT
            if src == "used":
                return "circle-check", C_FAINT   # 消化済み＝薄く
            return "circle-check", on_color
        if hasattr(self, 'mini_pos_dot'):
            if pos_flash and self._mini_mode:
                self._flash_mini_dot(self.mini_pos_dot, C_GREEN)
            else:
                self._set_mini_dot(self.mini_pos_dot,
                    *_mini_state(pos_ok, self._pos_source, C_GREEN))
        if hasattr(self, 'mini_neg_dot'):
            if neg_flash and self._mini_mode:
                self._flash_mini_dot(self.mini_neg_dot, C_RED)
            else:
                self._set_mini_dot(self.mini_neg_dot,
                    *_mini_state(neg_ok, self._neg_source, C_RED))
        if hasattr(self, 'ts_pos_lbl'):
            t = self._pos_received_time
            self.ts_pos_lbl.configure(
                text=(f"P {t}" if t else ""),
                text_color=C_GREEN if pos_ok else C_FAINT)
        if hasattr(self, 'ts_neg_lbl'):
            t = self._neg_received_time
            self.ts_neg_lbl.configure(
                text=(f"N {t}" if t else ""),
                text_color=C_RED if neg_ok else C_FAINT)


    def _set_status(self, msg, color=C_GRAY):

        self.status_lbl.configure(text=msg, text_color=color)


    def _enable_auto(self):

        self._auto_generate = True
        self._update_mode_status()
        self._refresh_go_btn()


    def _enable_manual(self):

        self._auto_generate = False
        self._update_mode_status()
        self._refresh_go_btn()


    def _refresh_go_btn(self):

        has_both = bool(self._positive and self._negative)
        has_pos  = bool(self._positive and not self._negative)
        if not self._positive:
            self.go_btn.configure(state="disabled", fg_color="#e6deea",
                                   hover_color="#ddd2e4", text_color=C_FAINT,
                                   image=ICON("wand-sparkles", C_FAINT, 20),
                                   text=self.S("go_waiting"))
        elif has_both:
            if self._auto_generate:
                self.go_btn.configure(state="normal", fg_color=C_AUTO,
                                       hover_color=C_GO_H, text_color="white",
                                       image=ICON("wand-sparkles", "white", 20),
                                       text=self.S("go_auto"))
            else:
                self.go_btn.configure(state="normal", fg_color=C_GO,
                                       hover_color=C_GO_H, text_color="white",
                                       image=ICON("wand-sparkles", "white", 20),
                                       text=self.S("go_manual"))
        elif has_pos:
            self.go_btn.configure(state="normal", fg_color=C_ACCENT,
                                   hover_color=C_PURPLE, text_color="white",
                                   image=ICON("wand-sparkles", "white", 20),
                                   text=self.S("go_pos_only"))


    def _on_go_btn(self):

        # 押した瞬間の欄の内容で生成する（KeyRelease取りこぼし対策の最終同期）
        self._on_box_edited("pos_box")
        self._on_box_edited("neg_box")
        if self._positive and not self._negative:
            self._generate_pos_only()
        else:
            self._generate()


    def _clear_pos(self):

        self._cancel_neg_skip()
        self._positive = ""; self._last_gen_key = ""; self._pos_source = None
        self._box_write(self.pos_box, "")
        self._update_recv_indicators(False, bool(self._negative))
        self._set_status(self.S("st_waiting"), C_ORANGE)
        self._refresh_go_btn()


    def _clear_neg(self):

        self._cancel_neg_skip()
        self._negative = ""; self._last_gen_key = ""; self._neg_source = None
        self._box_write(self.neg_box, "")
        self._update_recv_indicators(bool(self._positive), False)
        if self._positive:
            self._set_status(self.S("st_pos_only"), C_ORANGE)
        else:
            self._set_status(self.S("st_waiting"), C_ORANGE)
        self._refresh_go_btn()


    def _copy_text(self, box):

        self.clipboard_clear()
        self.clipboard_append(box.get("1.0","end").strip())


    def _apply_spice(self, pos):
        """チェックされたスパイスを全部ポジに追記して返す"""
        extras = []
        for i in range(1, 10):
            var = self._spice_checks.get(i)
            if var and var.get():
                entry = self._spice_entries.get(i)
                text = (entry.get().strip() if entry else "") or self.config_data.get(f"spice_{i}", "").strip()
                if text:
                    extras.append(text)
        if not extras:
            return pos
        if pos and not pos.endswith(","):
            pos += ","
        return (pos + " " + ", ".join(extras)).strip(", ")


    def _generate(self):

        if self._generating: return
        self._generating = True
        try:
            # self._positive を使う（ポジボックスにはスパイスが書き込まれてる場合があるため）
            raw_pos = self._positive or self.pos_box.get("1.0","end").strip()
            neg     = self._negative or self.neg_box.get("1.0","end").strip()
            if not raw_pos or not neg:
                self._generating = False
                return
            pos = self._apply_spice(raw_pos)
            self._do_generate(pos, neg, neg_empty=False, raw_pos=raw_pos)
        except Exception as e:
            # エラーで _generating が詰まらないよう確実にリセット
            self._generating = False
            self._set_status(self.S("st_gen_error", e=e), C_RED)
            print(f"[generate error] {e}")


    def _generate_pos_only(self):

        self._cancel_neg_skip()
        if not self._positive or self._generating: return
        self._generating = True
        try:
            pos = self._apply_spice(self._positive)
            self._do_generate(pos, "", neg_empty=True, raw_pos=self._positive)
        except Exception as e:
            self._generating = False
            self._set_status(self.S("st_gen_error", e=e), C_RED)
            print(f"[generate_pos_only error] {e}")






    def _do_generate(self, pos, neg, neg_empty=False, raw_pos=None):

        # ネガ補強スイッチがオンなら自動追記
        if not neg_empty and self._neg_boost_on.get():
            boost = self.config_data.get("neg_boost","").strip()
            if boost:
                if neg and not neg.endswith(","):
                    neg += ","
                neg = (neg + " " + boost).strip(", ")

        url = self.config_data.get("sd_url", "http://127.0.0.1:7860")
        try:
            cfg_val    = float(self.config_data.get("cfg", 7))
            width_val  = int(self.config_data.get("width", 1024))
            height_val = int(self.config_data.get("height", 1024))
        except:
            cfg_val, width_val, height_val = 7.0, 1024, 1024
        payload = {
            "prompt":         pos,
            "negative_prompt": neg,
            "steps":          int(self.config_data.get("steps", 28)),
            "cfg_scale":      cfg_val,
            "width":          width_val,
            "height":         height_val,
            "sampler_name":   self.config_data.get("sampler","DPM++ 2M Karras"),
        }
        self._set_status(self.S("st_generating"), C_PURPLE)
        self.go_btn.configure(state="disabled")
        self._show_pos_with_spice(raw_pos or pos, pos)
        self._set_gen_busy(True)
        threading.Thread(target=self._send, args=(url, payload, pos, neg, neg_empty, raw_pos or pos), daemon=True).start()


    def _send(self, url, payload, pos, neg, neg_empty, raw_pos):

        try:
            resp = requests.post(f"{url}/sdapi/v1/txt2img", json=payload, timeout=300)
            if resp.status_code == 200:
                images = resp.json().get("images",[])
                if images:
                    save_dir = self.config_data.get("save_dir","generated_images")
                    os.makedirs(save_dir, exist_ok=True)
                    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    out = os.path.join(save_dir, f"output_{ts}.png")
                    img_bytes = base64.b64decode(images[0])
                    with open(out,"wb") as f: f.write(img_bytes)
                    self._last_saved_path = out
                    self._last_gen_key    = raw_pos + "|||" + neg  # スパイス前のrawポジで比較
                    self._last_gen_time   = __import__('datetime').datetime.now().strftime("%H:%M:%S")
                    done_msg = self.S("st_done_pos") if neg_empty else self.S("st_done_both")
                    self.after(0, self._show_preview, img_bytes)
                    self.after(0, lambda o=out: self._set_fname_caption(o))
                    self.after(0, lambda: self._set_status(done_msg, C_GREEN))
                    self.after(0, lambda: self.open_file_btn.configure(state="normal"))
                    self.after(0, lambda: self.open_folder_btn.configure(state="normal"))
                    self.after(0, lambda o=out: self._select_newest_history(o))
                    self.after(0, self._refresh_history)
                    self.after(0, lambda rp=raw_pos: self._mark_prompts_used(rp))
                    _t = self._last_gen_time
                    self.after(0, lambda t=_t: hasattr(self, 'ts_gen_lbl') and
                        self.ts_gen_lbl.configure(text=f"✨ {t}" if t else ""))
                else:
                    self.after(0, lambda: self._set_status(self.S("st_gen_failed"), C_ORANGE))
            else:
                c = resp.status_code
                self.after(0, lambda: self._set_status(self.S("st_sd_error", c=c), "red"))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._set_status(self.S("st_sd_no_conn"), "red"))
        except Exception as e:
            _e = e
            self.after(0, lambda: self._set_status(self.S("st_gen_error", e=_e), "red"))
        finally:
            self._generating = False
            self.after(0, self._on_generate_done)

    def _show_pos_with_spice(self, raw_pos, pos_with_spice):
        """ポジボックスにスパイス追記部分を紫・太字で表示する
        （追記部分は編集を始めると_strip_spice_displayで自動的に外れる）"""
        try:
            tb = self.pos_box._textbox
            tb.delete("1.0", "end")
            tb.insert("end", raw_pos)
            if pos_with_spice != raw_pos:
                spice_part = pos_with_spice[len(raw_pos):]
                tb.tag_configure("spice_tag",
                    foreground=C_ACCENT, font=("Consolas", 11, "bold"))
                tb.insert("end", spice_part, "spice_tag")
        except Exception:
            pass

    def _on_generate_done(self):
        """生成完了後の後処理。ペンディングプロンプトがあれば自動生成する。"""
        self._set_gen_busy(False)
        self._refresh_go_btn()
        if self._pending_prompt and self._auto_generate:
            pos, neg, pos_only = self._pending_prompt
            self._pending_prompt = None
            if pos_only:
                self._generate_pos_only()
            else:
                key = pos + "|||" + neg
                if key != self._last_gen_key:
                    self._generate()
                else:
                    # 「生成完了後に生成するよ」と案内した手前、黙って捨てずに理由を出す
                    self._set_status(self.S("st_same_prompt"), C_ORANGE)
        else:
            self._pending_prompt = None

    # ── プレビュー ────────────────────────────────────
    def _set_preview_size(self, size, size_info):

        if size == "Hide":
            self._preview_hidden = not self._preview_hidden
            if self._preview_hidden:
                self._apply_hide_cover()
                if hasattr(self, "fname_cap"):
                    self.fname_cap.pack_forget()     # ファイル名も隠す
                self._refresh_history()              # 履歴サムネも隠す（hidden中は placeholder）
            else:
                self._refresh_history()              # 履歴サムネ復帰
                if self._last_img_bytes:
                    self._show_preview(self._last_img_bytes)
                    if self._last_saved_path:
                        self._set_fname_caption(self._last_saved_path)
                else:
                    self.preview_lbl.configure(text=self.S("preview_wait"))
            return
        was_hidden = self._preview_hidden   # S/M/L はサイズ変更＋非表示解除を兼ねる
        self._preview_hidden   = False
        self._preview_size     = size
        self._preview_size_info = size_info
        for sz, btn in self._sz_btns.items():
            btn.configure(fg_color=C_PINK if sz == size else "transparent",
                          text_color="white"  if sz == size else C_SUB)
        if was_hidden:
            self._refresh_history()             # 履歴サムネも一緒に復帰
            if self._last_saved_path:
                self._set_fname_caption(self._last_saved_path)
        if self._last_img_bytes:
            self._show_preview(self._last_img_bytes)
        else:
            self.preview_lbl.configure(text=self.S("preview_wait"))


    def _apply_hide_cover(self):

        si = getattr(self, "_preview_size_info", (280, 340))
        if self._mini_mode:
            si = self._mini_fit_size()
        if si is None:
            # Lサイズ（fill）のときはパネルサイズを使う
            panel = getattr(self, '_left_panel', None)
            if panel:
                w = max(panel.winfo_width()  - 40, 300)
                h = max(panel.winfo_height() - 120, 300)
            else:
                w, h = 500, 560
        else:
            w = si[0] if isinstance(si, tuple) else 280
            h = si[1] if isinstance(si, tuple) else 340
        cover = Image.new("RGB", (w, h), "#f0c0d8")
        try:
            from PIL import ImageDraw
            draw  = ImageDraw.Draw(cover)
            block = 20
            for y in range(0, h, block):
                for x in range(0, w, block):
                    c = "#f8d0e8" if (x//block + y//block) % 2 == 0 else "#e8b0cc"
                    draw.rectangle([x, y, x+block-1, y+block-1], fill=c)
        except: pass
        ctk_img = ctk.CTkImage(light_image=cover, size=(w, h))
        self._preview_image = ctk_img
        self.preview_lbl.configure(image=ctk_img, text="")


    def _show_preview(self, img_bytes):

        self._last_img_bytes = img_bytes
        if self._preview_hidden:
            self._apply_hide_cover(); return
        si = getattr(self, "_preview_size_info", (280, 340))
        if self._mini_mode:
            si = self._mini_fit_size()   # ミニはポラロイド風に窓いっぱい
        try:
            pil = Image.open(io.BytesIO(img_bytes))
            if si is None:
                # L = 左パネルのサイズいっぱいまで使う
                panel = getattr(self, '_left_panel', None)
                if panel:
                    pw = max(panel.winfo_width()  - 40, 300)
                    ph = max(panel.winfo_height() - 120, 300)
                else:
                    pw, ph = 500, 560
                ratio = min(pw / pil.width, ph / pil.height)
                si = (int(pil.width * ratio), int(pil.height * ratio))
            pil = pil.copy()
            pil.thumbnail(si, Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil, size=(pil.width, pil.height))
            self._preview_image = ctk_img
            self.preview_lbl.configure(image=ctk_img, text="")
        except Exception as e:
            self.preview_lbl.configure(text=f"Preview error: {e}")


    def _on_preview_click(self, _):

        if self._last_saved_path:
            try: os.startfile(self._last_saved_path)
            except: pass


    def _open_image_file(self):

        if self._last_saved_path:
            try: os.startfile(self._last_saved_path)
            except: pass


    def _open_save_folder(self):

        d = self.config_data.get("save_dir","")
        if d and os.path.exists(d):
            subprocess.Popen(["explorer", os.path.normpath(d)])


    def _open_manual(self):

        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base = os.getcwd()
        html = "MANUAL_JA.html" if self.lang == "ja" else "MANUAL_EN.html"
        p    = os.path.join(base, html)
        if os.path.exists(p):
            webbrowser.open(f"file:///{p.replace(os.sep, '/')}")

    # ── 設定保存 ──────────────────────────────────────
    def _browse(self):

        d = fd.askdirectory(title="Save folder")
        if d:
            self.save_entry.delete(0,"end")
            self.save_entry.insert(0, d)


    def _save_settings(self):

        for k, e in self.setting_entries.items():
            self.config_data[k] = e.get().strip()
        # スパイス入力欄の内容をconfig_dataへ反映
        for i in range(1, 10):
            entry = self._spice_entries.get(i)
            if entry:
                self.config_data[f"spice_{i}"] = entry.get().strip()
        # ネガ補強テンプレートも保存
        if hasattr(self, 'neg_boost_textbox'):
            self.config_data["neg_boost"] = self.neg_boost_textbox.get("1.0","end").strip()
        self._save_config()
        self._update_sd_status()
        self._refresh_history()
        self.save_result_lbl.configure(text=self.S("s_saved"), text_color=C_GREEN)
        self.after(3000, lambda: self.save_result_lbl.configure(text=""))

    def _copy_rules(self):
        """AIへのお約束.txt をクリップボードにコピー"""
        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base = os.getcwd()
        path = os.path.join(base, "AIへのお約束.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.clipboard_clear()
            self.clipboard_append(text)
            orig = self.status_lbl.cget("text")
            self._set_status("お約束をコピーしたよ！", C_ACCENT)
            self.after(2500, lambda o=orig: self.status_lbl.configure(text=o))
        except FileNotFoundError:
            self._set_status("❌ AIへのお約束.txt が見つからないよ", C_RED)

    # ── ミニモード ────────────────────────────────────
    def _toggle_mini(self):

        if not self._mini_mode:
            self._mini_mode   = True
            self._normal_geo  = self.geometry()
            self._spice_was_open = self._spice_panel_frame.winfo_ismapped()
            # 絵が主役：パネル・タイトルバー・ファイル名を全部隠す
            self._right_outer.pack_forget()
            if self._spice_was_open:
                self._spice_panel_frame.place_forget()
            self._sz_frame.pack_forget()
            if self._history_strip:
                self._history_strip.pack_forget()
            self._bot_bar.pack_forget()
            self._tbar.pack_forget()
            if hasattr(self, "fname_cap"):
                self.fname_cap.pack_forget()
            self._left_panel.pack_configure(padx=4, pady=4)   # ベゼル最小化
            self._mini_lamp_bar.pack(fill="x", padx=4, pady=(0, 4))
            # 前回のミニ位置・サイズを復元（初回は右下隅）
            self.minsize(280, 340)
            _g = self.config_data.get("mini_geometry", "")
            if not _g or "+" not in _g:
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                _g = f"300x360+{sw-330}+{sh-450}"
            self.geometry(_g)
            # pack変更直後はpositionが無視されることがあるので遅延で再適用
            self.after(150, lambda p="+" + _g.split("+", 1)[1]: self._mini_mode and self.geometry(p))
            self.attributes("-topmost", True)
            self.after(260, self._rescale_mini_preview)   # ポラロイド風に再フィット
            # ミニ時は自動生成固定
            self._auto_generate = True
            self._update_mode_status()
        else:
            self._mini_mode = False
            # ミニの位置・サイズを記憶（次回も同じ場所に出す）
            self.config_data["mini_geometry"] = self.geometry()
            self._save_config()
            self._mini_lamp_bar.pack_forget()
            self._left_panel.pack_configure(padx=(14, 6), pady=14)
            self._tbar.pack(fill="x", before=self._hairline)
            self._right_outer.pack(side="right", fill="y", padx=(0,14), pady=14)
            if self._spice_was_open:
                self._spice_panel_frame.place(relx=1.0, rely=0.0, anchor="ne",
                    relheight=1.0, x=-8, y=8)
            self._sz_frame.pack(pady=(2,2))
            if self._history_strip:
                self._history_strip.pack(fill="x", pady=(0,2))
            self._bot_bar.pack(fill="x", padx=14, pady=(6,14))
            self.minsize(1060, 720)
            self.geometry(self._normal_geo)
            if "+" in self._normal_geo:
                self.after(150, lambda p="+" + self._normal_geo.split("+", 1)[1]:
                    (not self._mini_mode) and self.geometry(p))
            self.attributes("-topmost", False)
            self._mini_btn.configure(text="Mini", image=ICON("pin", C_PINK, 16))
            # ファイル名キャプション・プレビューサイズ復帰
            if self._last_saved_path and not self._preview_hidden:
                self._set_fname_caption(self._last_saved_path)
            self.after(260, self._restore_preview_after_mini)

    # ウィンドウ閉じる
    def _on_close(self):

        try:
            if self._mini_mode:   # ミニのまま閉じても位置を記憶
                self.config_data["mini_geometry"] = self.geometry()
                self._save_config()
        except: pass
        try: self.destroy()
        except: pass
        os._exit(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
