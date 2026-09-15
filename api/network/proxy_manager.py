"""
Proxy Manager for ProxyBox
Manages Mitmproxy process and traffic interception
"""

import subprocess
import os
import signal
import time
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages Mitmproxy process for traffic interception
    """
    
    def __init__(
        self,
        port: int = 8080,
        script_path: str = "/app/api/mitmproxy/addon.py",
        ssl_insecure: bool = True
    ):
        self.port = port
        self.script_path = script_path
        self.ssl_insecure = ssl_insecure
        
        self.process: Optional[subprocess.Popen] = None
        self.addon = None
    
    def start(self) -> bool:
        """Start Mitmproxy process"""
        if self.process is not None:
            logger.warning("Mitmproxy is already running")
            return True
        
        try:
            cmd = [
                "mitmdump",
                "-s", self.script_path,
                "--listen-port", str(self.port),
                "--no-http2",
            ]
            
            if self.ssl_insecure:
                cmd.append("--ssl-insecure")
            
            logger.info(f"Starting Mitmproxy with command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name == 'posix' else None
            )
            
            # Wait for Mitmproxy to start
            time.sleep(2)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"Mitmproxy failed to start: {stderr.decode() if stderr else 'Unknown error'}")
                self.process = None
                return False
            
            logger.info(f"Mitmproxy started successfully on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Mitmproxy: {e}")
            self.process = None
            return False
    
    def stop(self) -> bool:
        """Stop Mitmproxy process"""
        if self.process is None:
            logger.warning("Mitmproxy is not running")
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
            
            logger.info("Mitmproxy stopped successfully")
            self.process = None
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Mitmproxy: {e}")
            self.process = None
            return False
    
    def restart(self) -> bool:
        """Restart Mitmproxy process"""
        self.stop()
        time.sleep(1)
        return self.start()
    
    def is_running(self) -> bool:
        """Check if Mitmproxy is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_proxy_url(self) -> str:
        """Get proxy URL"""
        return f"http://127.0.0.1:{self.port}"
    
    def get_pid(self) -> Optional[int]:
        """Get process ID"""
        if self.process is None:
            return None
        return self.process.pid
    
    def set_addon(self, addon):
        """Set reference to Mitmproxy addon"""
        self.addon = addon
        logger.info("ProxyManager connected to Mitmproxy addon")
