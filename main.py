from pathlib import Path
import dearpygui.dearpygui as dpg

class WinPireWall:
    def __init__(self):
        dpg.create_context()

        # NanumGothic.ttf 파일 경로
        self.FONT_PATH = str(Path(__file__).parent / "resources" / "NanumGothic.ttf")

        # 폰트 레지스트리 설정
        with dpg.font_registry():
            # 한글 폰트 설정
            with dpg.font(self.FONT_PATH, 20) as default_font:
                # Korean 언어 힌트 추가
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)

        with dpg.window(label="윈도우 방화벽"):
            dpg.add_text("Hello, Dear PyGui!")
            dpg.add_text("안녕하세요, 디어 파이구이!")
            
            dpg.add_button(label="저장")
            dpg.add_button(label="열기")
            dpg.add_button(label="닫기")

        # 기본 폰트 설정
        dpg.bind_font(default_font)

        dpg.set_primary_window(dpg.last_container(), True)
        dpg.create_viewport(title='win pirewall', width=1200, height=600)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def run(self):
        dpg.start_dearpygui()

if __name__ == "__main__":
    WinPireWall().run()