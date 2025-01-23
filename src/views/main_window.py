import sys
import dearpygui.dearpygui as dpg

# 한글 폰트 설정입니다.
from src.controllers.set_lang import set_kor
# 핫 리로드 기능입니다.
# from src.controllers.hot_reload import HotReloader

class MainWindow:
    def __init__(self):
        dpg.create_context()
        
        # 한글 폰트 설정
        set_kor()

        with dpg.window(tag="Main Window", label="윈도우 방화벽"):
            dpg.add_text("Hello, Dear PyGui!!")
            dpg.add_text("안녕하세요, 디어 파이구이!")  
            
            dpg.add_button(label="저장")
            dpg.add_button(label="열기")
            dpg.add_button(label="닫기")

        dpg.set_primary_window(dpg.last_container(), True)
        dpg.create_viewport(title='win pirewall', width=1200, height=600)
        dpg.setup_dearpygui()
        
    def run(self):
        try:
            dpg.show_viewport()
            dpg.start_dearpygui()
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            if dpg.is_dearpygui_running():
                dpg.stop_dearpygui()
            dpg.destroy_context()