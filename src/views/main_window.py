import atexit
import json
from pathlib import Path
import sys
import dearpygui.dearpygui as dpg
import signal


# 한글 폰트 설정입니다.
from src.controllers.set_lang import set_kor

class MainWindow:
    def __init__(self):
        self.window_config_file = Path("window_config.json")
        self.default_config = json.loads(Path("resources/default_window_config.json").read_text())
        
        dpg.create_context()
        set_kor()
        
        # 저장된 창 설정 불러오기
        self.config = self.load_window_config()

        with dpg.window(tag="main_window", label="윈도우 방화벽"):
            # 메뉴바 
            with dpg.menu_bar(tag="main_menu_bar"):
                
                with dpg.menu(label="파일"):
                    dpg.add_menu_item(label="새로 만들기", callback=lambda: print("새로 만들기"))
                    dpg.add_menu_item(label="열기", callback=lambda: print("열기"))
                    dpg.add_menu_item(label="저장", callback=lambda: print("저장"))
                    dpg.add_menu_item(label="종료", callback=lambda: dpg.stop_dearpygui())
                with dpg.menu(label="편집"):
                    dpg.add_menu_item(label="복사", callback=lambda: print("복사"))
                    dpg.add_menu_item(label="붙여넣기", callback=lambda: print("붙여넣기"))
                    dpg.add_menu_item(label="잘라내기", callback=lambda: print("잘라내기"))
                with dpg.menu(label="도움말"):
                    dpg.add_menu_item(label="정보", callback=lambda: print("정보"))
                    
            # 메뉴바 더블클릭 시 최대화
            
            # 탭바
            with dpg.tab_bar():
                with dpg.tab(label="기본설정"):
                    dpg.add_text("기본설정")
                with dpg.tab(label="포트설정"):
                    dpg.add_text("포트설정")
                with dpg.tab(label="프로그램설정"):
                    dpg.add_text("프로그램설정")
                with dpg.tab(label="로그"):
                    dpg.add_text("로그")
            
                
            

        dpg.set_primary_window("main_window", True)
        
        # 저장된 위치와 크기로 viewport 생성
        dpg.create_viewport(
            title='win pirewall',
            width=self.config["width"],
            height=self.config["height"],
            x_pos=self.config["x"],
            y_pos=self.config["y"]
        )
        self.set_viewport_config()
        
        
        dpg.setup_dearpygui()
        # 시그널 핸들러 설정
        self.setup_signal_handlers()
        # 프로그램 종료 시 cleanup 실행
        atexit.register(self.cleanup)  
        
    
            
    def setup_signal_handlers(self):
        """
        SIGINT 및 SIGTERM 신호에 대한 핸들러를 설정합니다.
        이 메서드는 SIGINT 및 SIGTERM 신호가 발생할 때 호출될 핸들러를 설정합니다.
        """
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGBREAK, self.signal_handler)  # Windows Ctrl+Break
        
    def signal_handler(self, signum, frame):
        """
        지정된 시그널을 처리하는 핸들러 함수입니다.
        시그널이 감지되면 설정을 저장하고 프로그램을 종료합니다.
        Args:
            signum (int): 감지된 시그널 번호.
            frame (FrameType): 현재 스택 프레임.
        """
        
        print(f"\n시그널 {signum} 감지됨, 설정 저장 후 종료...")
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """
        Dear PyGui 정리 및 창 설정 저장
        """
        if hasattr(self, '_cleanup_done'):  # 중복 실행 방지 
            return
            
        if dpg.is_dearpygui_running():
            try:
                self.save_window_config()
                dpg.stop_dearpygui()
            except (RuntimeError, AttributeError) as e:
                print(f"DPG 종료 중 오류 발생: {e}")  # 로깅을 위한 출력
            
        try:
            dpg.destroy_context()
        except (RuntimeError, AttributeError) as e:
            print(f"DPG 컨텍스트 제거 중 오류 발생: {e}")
            
        self._cleanup_done = True
        
    def set_viewport_config(self):
        """
        설정된 구성에 따라 뷰포트의 속성을 설정합니다.
        설정 항목:
        - is_viewport_always_top: 뷰포트를 항상 최상위에 유지할지 여부
        - is_viewport_resizable: 뷰포트 크기 조정 가능 여부
        - is_viewport_decorated: 뷰포트에 장식(테두리 등)을 표시할지 여부
        - is_viewport_vsync_on: 뷰포트에서 VSync를 활성화할지 여부
        """
        dpg.set_viewport_always_top(self.config["is_viewport_always_top"])
        dpg.set_viewport_resizable(self.config["is_viewport_resizable"])
        dpg.configure_viewport(0, decorated=self.config["is_viewport_decorated"])
        dpg.set_viewport_vsync(self.config["is_viewport_vsync_on"])
        
    def load_window_config(self):
        """
        창 설정 파일을 로드합니다.
        설정 파일이 존재하지 않거나 로드 중 오류가 발생하면 기본 설정을 반환합니다.
        Returns:
            dict: 창 설정을 담고 있는 딕셔너리.
        """
        try:
            if self.window_config_file.exists():
                with open(self.window_config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 누락된 설정은 기본값으로 대체
                    merged_config = self.default_config.copy()
                    merged_config.update(loaded_config)
                    return merged_config
        except Exception as e:
            print(f"설정 파일 로딩 실패: {str(e)}")
        return self.default_config.copy()
        
    def save_window_config(self):
        """
        현재 창 구성을 JSON 파일에 저장합니다.
        이 메서드는 현재 뷰포트 위치, 크기 및 항상 위에 표시, 크기 조정 가능, 장식 여부, vsync 상태와 같은
        다양한 설정을 가져옵니다. 그런 다음 이러한 설정을 `self.window_config_file`로 지정된 JSON 파일에 저장합니다.
        예외:
            Exception: 구성 파일을 저장하는 동안 오류가 발생한 경우.
        """
        
        try:
            viewport_pos = dpg.get_viewport_pos()
            
            config = {
                "x": viewport_pos[0],
                "y": viewport_pos[1],
                "width": dpg.get_viewport_width(),
                "height": dpg.get_viewport_height(),
                "is_viewport_always_top": dpg.is_viewport_always_top(),
                "is_viewport_resizable": dpg.is_viewport_resizable(),
                "is_viewport_decorated": dpg.is_viewport_decorated(),
                "is_viewport_vsync_on": dpg.is_viewport_vsync_on(),
            }
            print(f"창 설정 저장: {config}")
            with open(self.window_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    def run(self):
        """
        메인 윈도우를 실행합니다.
        Dear PyGui의 뷰포트를 표시하고 이벤트 루프를 시작합니다.
        실행 중 오류가 발생하면 예외를 출력합니다.
        마지막으로 cleanup 메서드를 호출하여 정리 작업을 수행합니다.
        """
        
        try:
            dpg.show_viewport()
            dpg.start_dearpygui()
        except Exception as e:
            print(f"실행 중 오류 발생: {str(e)}")
        finally:
            self.cleanup()