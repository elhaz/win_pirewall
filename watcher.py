import os
import subprocess
import signal
import sys
import time
import psutil
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.last_restart = 0
        self.cooldown = 1  # 1초 쿨다운
        self.start_process()

    def start_process(self):
        """Start the process."""
        if self.process is None:
            print("Starting process...")
            self.process = subprocess.Popen(self.command.split())
            self.last_restart = time.time()

    def stop_process(self):
        if self.process:
            try:
                parent = psutil.Process(self.process.pid)
                
                # DearPyGui 정상 종료 시도
                try:
                    if dpg.is_dearpygui_running():
                        dpg.stop_dearpygui()
                    dpg.destroy_context()
                except:
                    pass

                # CTRL+C 시그널 전송
                parent.send_signal(signal.SIGINT)
                
                # 정상 종료 대기
                try:
                    parent.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # 자식 프로세스 강제 종료
                    for child in parent.children(recursive=True):
                        child.kill()
                    # 부모 프로세스 강제 종료
                    parent.kill()
                
                print("Process stopped.")
                self.process = None
                
            except psutil.NoSuchProcess:
                print("Process already terminated.")
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
    """Watch the given directory for changes and restart the process."""
    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    try:
        print(f"Watching directory: {directory}")
        print("Press Ctrl+C to stop...")
        observer.join()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        # 프로세스 종료
        event_handler.stop_process()
        # 옵저버 정리
        observer.stop()
        observer.join()
        print("Watcher stopped successfully..")
        sys.exit(0)

if __name__ == "__main__":
    # 변경을 감지할 디렉터리
    watch_dir = "./"  # 현재 디렉터리
    # 실행할 명령어 (예: Python 프로젝트 실행)
    command = "uv run main.py"
    # 디렉터리 감시 시작
    watch_directory(watch_dir, command)
