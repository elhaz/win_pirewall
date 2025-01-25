import json
from pathlib import Path
import sys
import dearpygui.dearpygui as dpg

# 한글 폰트 설정입니다.
from src.controllers.set_lang import set_kor

class MainWindow:
    def __init__(self):
        self.window_config_file = Path("window_config.json")
        self.default_config = {
            "x": 100,
            "y": 100,
            "width": 1200,
            "height": 600
        }
        
        dpg.create_context()
        set_kor()
        
        # 저장된 창 설정 불러오기
        self.config = self.load_window_config()

        with dpg.window(tag="Main Window", label="윈도우 방화벽"):
            dpg.add_text("Hello, Dear PyGui!!")
            dpg.add_text("안녕하세요, 디어 파이구이!!!!")  
            
            dpg.add_button(label="저장")
            dpg.add_button(label="열기")
            dpg.add_button(label="닫기")

        dpg.set_primary_window(dpg.last_container(), True)
        
        # 저장된 위치와 크기로 viewport 생성
        dpg.create_viewport(
            title='win pirewall',
            width=self.config["width"],
            height=self.config["height"],
            x_pos=self.config["x"],
            y_pos=self.config["y"]
        )
        dpg.setup_dearpygui()
        
    def load_window_config(self):
        try:
            if self.window_config_file.exists():
                with open(self.window_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"설정 파일 로딩 실패: {e}")
        return self.default_config
        
    def save_window_config(self):
        try:
            viewport_pos = dpg.get_viewport_pos()
            
            config = {
                "x": viewport_pos[0],
                "y": viewport_pos[1],
                "width": dpg.get_viewport_width(),
                "height": dpg.get_viewport_height()
            }
            
            with open(self.window_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    def run(self):
        try:
            dpg.show_viewport()
            dpg.start_dearpygui()
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            if dpg.is_dearpygui_running():
                self.save_window_config()  # 종료 전 창 위치 저장
                dpg.stop_dearpygui()
            dpg.destroy_context()