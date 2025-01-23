import os
import subprocess
import signal
import sys
import time
import psutil
import signal
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
        self.cooldown = 1
        self.window_pos_file = 'window_position.json'
        self.window_title = None  # 윈도우 타이틀 저장 변수
        self.start_process()
        
    def find_window_title(self):
        if self.process:
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    # 프로세스 ID로 매칭
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)  # win32process 사용
                    if pid == self.process.pid:
                        self.window_title = title
                        return False
            win32gui.EnumWindows(callback, None)
        
    def save_window_position(self):
        if self.process and self.window_title:
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if self.window_title == title:
                        rect = win32gui.GetWindowRect(hwnd)
                        pos = {
                            'title': self.window_title,
                            'x': rect[0],
                            'y': rect[1],
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1]
                        }
                        with open(self.window_pos_file, 'w') as f:
                            json.dump(pos, f)
                        return False
            win32gui.EnumWindows(callback, None)
            
    def restore_window_position(self):
        try:
            with open(self.window_pos_file, 'r') as f:
                pos = json.load(f)
                self.window_title = pos.get('title')
                
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if self.window_title == title:
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP,
                                            pos['x'], pos['y'],
                                            pos['width'], pos['height'],
                                            win32con.SWP_SHOWWINDOW)
                        return False
            time.sleep(0.5)
            win32gui.EnumWindows(callback, None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def start_process(self):
        if self.process is None:
            print("Starting process...")
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            self.process = subprocess.Popen(
                self.command.split(),
                creationflags=CREATE_NEW_PROCESS_GROUP
            )
            self.last_restart = time.time()
            time.sleep(1)  # 윈도우가 생성될 때까지 대기
            self.find_window_title()  # 윈도우 타이틀 찾기
            self.restore_window_position()
            
    def stop_process(self):
        if self.process:
            try:
                self.save_window_position()
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                
                parent.terminate()
                
                # 최대 3초 동안 종료 대기
                gone, alive = psutil.wait_procs([parent], timeout=3)
                
                # 여전히 살아있는 프로세스 강제 종료
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

    def on_any_event(self, event):
        """Restart the process on Python file changes."""
        if event.is_directory:
            return
            
        # .py 파일만 처리
        if not event.src_path.endswith('.py'):
            return
            
        # 쿨다운 체크
        current_time = time.time()
        if current_time - self.last_restart < self.cooldown:
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
