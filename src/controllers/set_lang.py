from pathlib import Path
import dearpygui.dearpygui as dpg

def set_kor_lang():
    # NanumGothic.ttf 파일 경로
    FONT_PATH = str(Path(__file__).parent.parent.parent / "resources" / "NanumGothic.ttf")

    # 폰트 레지스트리 설정
    with dpg.font_registry():
        # 한글 폰트 설정
        with dpg.font(FONT_PATH, 20) as default_font:
            # Korean 언어 힌트 추가
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)
            
    # 기본 폰트 설정
    dpg.bind_font(default_font)