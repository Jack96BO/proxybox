"""
Chromium Process Manager
Handles Chromium standalone process with CDP support
"""

import subprocess
import os
import signal
import time
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class ChromiumProcess:
    """
    Manages Chromium standalone process with remote debugging port
    """
    
    def __init__(
        self,
        cdp_port: int = 9222,
        proxy_server: Optional[str] = None,
        user_data_dir: str = "/data/chromium",
        headless: bool = True,
        no_sandbox: bool = True,
        disable_gpu: bool = True
    ):
        self.cdp_port = cdp_port
        self.proxy_server = proxy_server
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.no_sandbox = no_sandbox
        self.disable_gpu = disable_gpu
        
        self.process: Optional[subprocess.Popen] = None
        self.cdp_url: Optional[str] = None
        
        # Ensure user data directory exists
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
    
    def _build_command(self) -> List[str]:
        """Build Chromium command with all arguments"""
        cmd = [
            "chromium",
            f"--remote-debugging-port={self.cdp_port}",
            f"--user-data-dir={self.user_data_dir}",
        ]
        
        if self.headless:
            cmd.append("--headless=new")
        
        if self.proxy_server:
            cmd.append(f"--proxy-server={self.proxy_server}")
        
        if self.no_sandbox:
            cmd.extend(["--no-sandbox", "--disable-setuid-sandbox"])
        
        if self.disable_gpu:
            cmd.append("--disable-gpu")
        
        # Additional security/stability flags for Docker
        cmd.extend([
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-hang-monitor",
            "--disable-ipc-flooding-protection",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-renderer-backgrounding",
            "--disable-sync",
            "--metrics-recording-only",
            "--mute-audio",
            "--use-gl=swiftshader",
        ])
        
        # Ignore certificate errors for Mitmproxy
        cmd.extend([
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--allow-running-insecure-content",
        ])
        
        return cmd
    
    def start(self) -> bool:
        """Start Chromium process"""
        if self.process is not None:
            logger.warning("Chromium is already running")
            return True
        
        try:
            cmd = self._build_command()
            logger.info(f"Starting Chromium with command: {' '.join(cmd)}")
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "DISPLAY": ":99",
                "LANG": "C.UTF-8",
                "LANGUAGE": "en_US:en",
            })
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid if os.name == 'posix' else None
            )
            
            # Wait for CDP to be ready
            self.cdp_url = f"http://127.0.0.1:{self.cdp_port}"
            
            # Check if process started successfully
            time.sleep(2)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"Chromium failed to start: {stderr.decode() if stderr else 'Unknown error'}")
                self.process = None
                return False
            
            logger.info(f"Chromium started successfully, CDP available at {self.cdp_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Chromium: {e}")
            self.process = None
            return False
    
    def stop(self) -> bool:
        """Stop Chromium process"""
        if self.process is None:
            logger.warning("Chromium is not running")
            return True
        
        try:
            # Try graceful shutdown first
            if os.name == 'posix':
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()
            
            # Wait for process to stop
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if not stopped
                if os.name == 'posix':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait(timeout=5)
            
            logger.info("Chromium stopped successfully")
            self.process = None
            self.cdp_url = None
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Chromium: {e}")
            self.process = None
            self.cdp_url = None
            return False
    
    def restart(self) -> bool:
        """Restart Chromium process"""
        self.stop()
        time.sleep(1)
        return self.start()
    
    def is_running(self) -> bool:
        """Check if Chromium is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_cdp_url(self) -> Optional[str]:
        """Get CDP URL"""
        return self.cdp_url
    
    def get_pid(self) -> Optional[int]:
        """Get process ID"""
        if self.process is None:
            return None
        return self.process.pid
