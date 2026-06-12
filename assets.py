# ══════════════════════════════════════════════
#  assets.py  —  アイコンローダー
#  Lucide icons (https://lucide.dev) / ISC License
#  SVGを初回だけ取得し、指定色の透過PNGに変換してキャッシュする。
#  2回目以降はディスクキャッシュから読むのでオフラインでも動作。
# ══════════════════════════════════════════════
import os, io, urllib.request
from PIL import Image

try:
    import customtkinter as ctk
except Exception:
    ctk = None

_BASE     = os.path.dirname(os.path.abspath(__file__))
ICON_DIR  = os.path.join(_BASE, "assets", "icons")
SVG_DIR   = os.path.join(ICON_DIR, "_svg")
CDN       = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{}.svg"
_CACHE    = {}          # (name,color,size) -> CTkImage
_SUPER    = 128         # 高解像度で描いてから縮小（アンチエイリアス用）


def _svg_text(name):
    """SVGをローカルキャッシュ→無ければCDNから取得して保存"""
    p = os.path.join(SVG_DIR, name + ".svg")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    os.makedirs(SVG_DIR, exist_ok=True)
    txt = urllib.request.urlopen(CDN.format(name), timeout=20).read().decode("utf-8")
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)
    return txt


_NAMED = {"white": (255, 255, 255), "black": (0, 0, 0)}

def _hex_rgb(c):
    if isinstance(c, tuple):
        return c
    c = c.strip()
    if c.lower() in _NAMED:               # 名前色（white/black）も許可
        return _NAMED[c.lower()]
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _render_png(name, color, px):
    """SVGを黒線で描画→輝度反転をαにして着色→透過PNGを返す（PIL Image）"""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    svg = _svg_text(name).replace("currentColor", "#000000")
    d = svg2rlg(io.BytesIO(svg.encode("utf-8")))
    d.width = _SUPER; d.height = _SUPER
    d.scale(_SUPER / 24.0, _SUPER / 24.0)
    gray  = renderPM.drawToPIL(d, bg=0xFFFFFF).convert("L")
    alpha = Image.eval(gray, lambda v: 255 - v)          # 黒線=不透明
    solid = Image.new("RGBA", gray.size, _hex_rgb(color) + (0,))
    solid.putalpha(alpha)
    return solid.resize((px, px), Image.LANCZOS)


def pil_icon(name, color="#E85D9A", size=18):
    """着色済み透過アイコンを PIL.Image で返す（PNGディスクキャッシュ利用）"""
    safe = color.lstrip("#")
    png  = os.path.join(ICON_DIR, f"{name}__{safe}__{size}.png")
    if os.path.exists(png):
        return Image.open(png).convert("RGBA")
    im = _render_png(name, color, size)
    os.makedirs(ICON_DIR, exist_ok=True)
    im.save(png)
    return im


def icon(name, color="#E85D9A", size=18):
    """CTkImage を返す（失敗時 None → 呼び出し側はテキストにフォールバック）"""
    key = (name, color, size)
    if key in _CACHE:
        return _CACHE[key]
    try:
        im = pil_icon(name, color, size)
        ck = ctk.CTkImage(light_image=im, dark_image=im, size=(size, size))
        _CACHE[key] = ck
        return ck
    except Exception as e:
        print(f"[assets.icon] '{name}' 失敗: {e}")
        return None


def prefetch(specs):
    """(name,color,size) のリストをまとめて生成（初回セットアップ用）"""
    ok = 0
    for name, color, size in specs:
        try:
            pil_icon(name, color, size); ok += 1
        except Exception as e:
            print(f"[prefetch] {name} 失敗: {e}")
    return ok


if __name__ == "__main__":
    # 単体実行で必要アイコンを一括生成
    PINK="#E85D9A"; PURPLE="#9B6BD6"; GRAY="#9A8FA6"; WHITE="#FFFFFF"
    GREEN="#36B98B"; RED="#F0617E"; AMBER="#F2A93C"; INK="#3A343F"
    names = ["folder","image","book-open","scroll-text","settings","refresh-cw",
             "sparkles","shield-check","languages","pin","copy","x","circle",
             "circle-check","circle-dot","zap","eye","gem","wand-sparkles",
             "heart","plug","trash-2","star","chevron-right","chevron-left",
             "loader","check","clipboard-copy","maximize-2"]
    specs=[]
    for n in names:
        for c in (PINK,PURPLE,GRAY,WHITE,GREEN,RED,AMBER,INK):
            specs.append((n,c,40))
    print("prefetch:", prefetch(specs), "/", len(specs))
