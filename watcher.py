import os
import subprocess
import sys
import time
import psutil
import json
import win32gui
import win32con
import win32process  # 추가
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.last_restart = 0
        self.cooldown = 2
        self.window_pos_file = 'watcherdata.json'
        self.window_title = None
        self.last_modified_time = {}
        
        # 초기 JSON 파일 생성
        if not os.path.exists(self.window_pos_file):
            with open(self.window_pos_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        
        self.start_process()
        
    def find_window_title(self):
        if self.process:
            time.sleep(2)
            found_windows = []
            
            # 자식 프로세스를 포함한 모든 관련 프로세스 ID 수집
            process_ids = set()
            try:
                parent = psutil.Process(self.process.pid)
                process_ids.add(parent.pid)
                
                # 자식 프로세스 추가
                children = parent.children(recursive=True)
                for child in children:
                    process_ids.add(child.pid)
                    
                print(f"검사할 프로세스 ID들: {process_ids}")
            except Exception as e:
                print(f"프로세스 검색 중 오류: {e}")
            
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if title.strip():
                            found_windows.append((title, pid))
                            
                        if pid in process_ids:
                            self.window_title = title
                            print(f"✅ 찾은 윈도우: {title} (PID: {pid})")
                            return False
                    except Exception as e:
                        print(f"창 검사 중 오류: {e}")
                        return True
            
            win32gui.EnumWindows(callback, None)
            
            if not self.window_title:
                print("\n🔍 발견된 모든 창 목록:")
                for title, pid in found_windows:
                    print(f"- {title} (PID: {pid})")
                print(f"\n❌ 프로세스 {process_ids}의 창을 찾지 못했습니다")
        
    def save_window_position(self):
        if self.process and self.window_title:
            try: 
                def callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        
                        # 프로세스 ID와 타이틀 모두 확인
                        if title == self.window_title:
                            rect = win32gui.GetWindowRect(hwnd)
                            pos_data = {
                                'title': title,
                                'x': rect[0],
                                'y': rect[1],
                                'width': rect[2] - rect[0],
                                'height': rect[3] - rect[1]
                            }
                            
                            # 파일 저장 시도
                            try:
                                with open(self.window_pos_file, 'w', encoding='utf-8') as f:
                                    json.dump(pos_data, f, ensure_ascii=False, indent=4)
                                print(f"✅ 윈도우 위치 저장됨: {pos_data}")
                                return False
                            except Exception as e:
                                print(f"❌ 파일 저장 중 오류: {e}")
                                return True
                    return True
                
                win32gui.EnumWindows(callback, None)
                
            except Exception as e:
                print(f"❌ 윈도우 위치 저장 중 오류: {e}")
            
    def restore_window_position(self):
        try:
            with open(self.window_pos_file, 'r') as f:
                pos = json.load(f)
                self.window_title = pos.get('title')
                print(f"Restoring window position for: {self.window_title}")
                
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if self.window_title == title:
                        print(f"Found window: {title}")
                        # 기존 윈도우 스타일 유지를 위한 플래그
                        flags = win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
                        try:
                            win32gui.SetWindowPos(
                                hwnd, 
                                win32con.HWND_TOP,
                                pos['x'], 
                                pos['y'],
                                pos['width'], 
                                pos['height'],
                                flags
                            )
                            print("Window position restored successfully")
                        except Exception as e:
                            print(f"Error restoring window position: {e}")
                        return False
                        
            # 윈도우가 완전히 생성될 때까지 충분히 대기
            time.sleep(1.5)
            win32gui.EnumWindows(callback, None)
            
        except FileNotFoundError:
            print("No saved window position found")
        except Exception as e:
            print(f"Error in restore_window_position: {e}")

    def start_process(self):
        if self.process is None:
            print("프로세스 시작 중...")
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            
            try:
                # 프로세스 시작
                self.process = subprocess.Popen(
                    self.command.split(),
                    creationflags=CREATE_NEW_PROCESS_GROUP
                )
                print(f"프로세스 PID: {self.process.pid}")
                
                # 윈도우가 완전히 생성될 때까지 충분히 대기
                time.sleep(4)  # 창을 찾기 전에 대기 시간을 조금 더 늘림
                
                # 여러 번 시도
                max_attempts = 3
                for attempt in range(max_attempts):
                    print(f"윈도우 찾기 시도 {attempt + 1}/{max_attempts}")
                    self.find_window_title()
                    if self.window_title:
                        break
                    time.sleep(1)
                
                if self.window_title:
                    print(f"윈도우 찾기 성공: {self.window_title}")
                    self.restore_window_position()
                else:
                    print("최대 시도 횟수를 초과했습니다.")
                
            except Exception as e:
                print(f"프로세스 시작 중 오류: {e}")
            
    def stop_process(self):
        if self.process:
            try:
                # 프로세스 종료 전에 윈도우 위치 저장
                self.save_window_position()
                
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                
                parent.terminate()
                gone, alive = psutil.wait_procs([parent], timeout=3)
                
                for p in alive:
                    p.kill()
                    
                print("Process stopped.")
                self.process = None
                
            except psutil.NoSuchProcess:
                print("Process already terminated.")
                self.process = None
            except Exception as e:
                print(f"Error stopping process: {e}")
                self.process = None

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.py'):
            return
        print(f"Python file changed: {event.src_path}")
        self.stop_process()
        self.start_process()

def watch_directory(directory, command):
    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.daemon = True  # 데몬 스레드로 설정
    observer.start()

    try:
        print(f"Watching directory: {directory}")
        print("Press Ctrl+C to stop...")
        while observer.is_alive():
            observer.join(1)  # 1초마다 체크
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        # 프로세스 종료
        event_handler.stop_process()
        # 옵저버 정리
        observer.stop()
        observer.join(timeout=3)  # 3초 타임아웃 설정
        if observer.is_alive():
            print("Observer did not stop cleanly, forcing exit...")
        print("Watcher stopped successfully..")
        sys.exit(0)

if __name__ == "__main__":
    # 변경을 감지할 디렉터리
    watch_dir = "./"  # 현재 디렉터리
    # 실행할 명령어 (예: Python 프로젝트 실행)
    command = "uv run main.py"
    # 디렉터리 감시 시작
    watch_directory(watch_dir, command)
