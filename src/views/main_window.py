import atexit
import json
from pathlib import Path
import sys
import dearpygui.dearpygui as dpg
import signal

# 한글 폰트 설정입니다.
from src.controllers.set_lang import set_kor_lang

class MainWindow:
    def __init__(self):
        self.window_config_file = Path("window_config.json")
        self.default_config = json.loads(Path("resources/default_window_config.json").read_text())
        dpg.create_context()
        set_kor_lang()
        
        # 저장된 창 설정 불러오기
        self.config = self.load_window_config()
        self.WSIZE = {
            "PATH_SET": 350,
            "LIST_SET": 350,
        }

        with dpg.window(tag="main_window", label="윈도우 방화벽"):
            
            # 좌우로 그룹 분리
            with dpg.group(horizontal=True):
                
                with dpg.child_window(tag="path_set", width=self.WSIZE["PATH_SET"], delay_search=True):
                    with dpg.group():
                        
                        dpg.add_text("프로그램 설정")
                        dpg.add_input_text(label="Rule Key", hint="Rule Key")
                        dpg.add_input_text(label="Log Path", hint="..\\access.log")
                        dpg.add_separator()
                        dpg.add_separator()
                        
                        dpg.add_text("Export")
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="제외패턴")
                            dpg.add_button(label="안티패턴")
                            dpg.add_button(label="차단목록")
                        dpg.add_separator()
                        dpg.add_separator()
                        
                        dpg.add_text("Import")
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="제외패턴")
                            dpg.add_button(label="안티패턴")
                            dpg.add_button(label="차단목록")
                        dpg.add_separator()
                        dpg.add_separator()
                        
                        dpg.add_text("DEBUG")
                        dpg.add_button(
                            label="제외목록에 더미추가", 
                            callback=self.debug.add_dummy_exclude
                        )
                        dpg.add_separator()
                        dpg.add_separator()
                        
                            
                        
                with dpg.child_window(tag="list_set", width=self.WSIZE["LIST_SET"], delay_search=True):
                    # 탭 - [제외목록, 안티패턴, 차단목록]
                    with dpg.tab_bar(tag="tab_bar"):
                        with dpg.tab(label="제외목록", tag="tab_exclude"):
                            
                            # 제외목록 입력, 추가버튼
                            with dpg.group(horizontal=True):
                                dpg.add_input_text(hint="제외패턴")
                                dpg.add_button(label="추가")
                                # 작은 텍스트. 제외목록의 테이블에 표시된 요소의 갯수.
                                dpg.add_text(label="0", tag="exclude_count")
                                
                            # 제외목록 테이블. 목록의 각 요소에 대하여 마우스오버시 삭제버튼 표시
                            with dpg.table(
                                tag="exclude_table",
                                header_row=False, 
                                no_host_extendX=True, 
                                no_host_extendY=True,
                                delay_search=True,
                                borders_innerH=True, borders_outerH=True, 
                                borders_innerV=False,borders_outerV=True, 
                                context_menu_in_body=True, row_background=True,
                                policy=dpg.mvTable_SizingFixedFit, 
                                height=-1, scrollY=True):
                                
                                dpg.add_table_column(label="target", init_width_or_weight=280)
                                dpg.add_table_column(label="delete")
                                
                            
                                    
                        with dpg.tab(label="안티패턴"):
                            dpg.add_input_text(label="안티패턴", hint="안티패턴")
                            
                        with dpg.tab(label="차단목록"):
                            dpg.add_input_text(label="차단목록", hint="차단목록")
                    
                    # tab_bar 내의 tab label 을 각 tab의 label 길이에 맞게 조정
                    # dpg.set_item_width("tab_exclude", 100)
                    # dpg.set_item_width("tab_anti", 100)
                    # dpg.set_item_width("tab_block", 100)
                    
                        
                with dpg.child_window(autosize_x=True, delay_search=True):
                    dpg.add_input_text(tag="logbox", multiline=True, height=-1, width=-1, readonly=True)
                    
                    
                
            
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
            
    class debug:
        @staticmethod
        def add_dummy_exclude():
            """
            제외목록에 더미 데이터를 추가합니다.
            """
            print("더미 데이터 추가")
            # exclude_table 에 1row 추가
            with dpg.table_row(parent="exclude_table"):
                dpg.add_text("dummy")
                dpg.add_button(label="delete")
            
            
    