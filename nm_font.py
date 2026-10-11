import os, sys
def _find_font():
    env = os.environ.get("NOUNAI_FONT")
    cands = ([env] if env else []) + [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "C:/Windows/Fonts/meiryob.ttc", "C:/Windows/Fonts/msgothic.ttc"]
    for p in cands:
        if p and os.path.exists(p): return p
    sys.exit("日本語フォントが見つかりません。NOUNAI_FONT にフォントファイルのパスを入れてください（Linuxなら apt install fonts-noto-cjk）。")
FONT = _find_font()
