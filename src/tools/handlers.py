import subprocess
import tempfile
import os
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CodeExecutionResult:
    success: bool
    output: str
    error: Optional[str]
    exit_code: int


class CodeExecutor:
    """Tool for executing code snippets safely"""
    
    ALLOWED_LANGUAGES = {"python", "javascript", "bash", "sql"}
    TIMEOUT = 30  # seconds
    
    async def execute(
        self,
        code: str,
        language: str,
        working_dir: Optional[str] = None,
    ) -> CodeExecutionResult:
        if language.lower() not in self.ALLOWED_LANGUAGES:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Language '{language}' not allowed. Allowed: {self.ALLOWED_LANGUAGES}",
                exit_code=-1,
            )
        
        try:
            if language.lower() == "python":
                return await self._execute_python(code, working_dir)
            elif language.lower() == "javascript":
                return await self._execute_javascript(code, working_dir)
            elif language.lower() == "bash":
                return await self._execute_bash(code, working_dir)
            elif language.lower() == "sql":
                return CodeExecutionResult(
                    success=False,
                    output="",
                    error="SQL execution requires database connection",
                    exit_code=-1,
                )
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
            )
    
    async def _execute_python(self, code: str, working_dir: Optional[str]) -> CodeExecutionResult:
        return await self._execute_subprocess(
            code, "python", "-c", working_dir
        )
    
    async def _execute_javascript(self, code: str, working_dir: Optional[str]) -> CodeExecutionResult:
        return await self._execute_subprocess(
            code, "node", "-e", working_dir
        )
    
    async def _execute_bash(self, code: str, working_dir: Optional[str]) -> CodeExecutionResult:
        if os.name == "nt":  # Windows
            return await self._execute_subprocess(
                code, "cmd", "/c", working_dir
            )
        else:
            return await self._execute_subprocess(
                code, "bash", "-c", working_dir
            )
    
    async def _execute_subprocess(
        self,
        code: str,
        executable: str,
        flag: str,
        working_dir: Optional[str],
    ) -> CodeExecutionResult:
        try:
            process = await asyncio.create_subprocess_exec(
                executable, flag, code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.TIMEOUT
            )
            
            return CodeExecutionResult(
                success=process.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace") if process.returncode != 0 else None,
                exit_code=process.returncode or 0,
            )
        except asyncio.TimeoutError:
            process.kill()
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.TIMEOUT} seconds",
                exit_code=-1,
            )


class FileHandler:
    """Tool for file operations"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None,
                }
            
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return {
                    "success": False,
                    "error": f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})",
                    "content": None,
                }
            
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "file_path": file_path,
                "file_size": file_size,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None,
            }
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content.encode("utf-8")),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def list_directory(self, dir_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(dir_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {dir_path}",
                    "files": [],
                }
            
            files = os.listdir(dir_path)
            file_info = []
            
            for f in files:
                full_path = os.path.join(dir_path, f)
                file_info.append({
                    "name": f,
                    "is_file": os.path.isfile(full_path),
                    "is_dir": os.path.isdir(full_path),
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None,
                })
            
            return {
                "success": True,
                "directory": dir_path,
                "files": file_info,
                "count": len(file_info),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": [],
            }


class WebSearch:
    """Tool for web search capabilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SEARCH_API_KEY")
    
    async def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the web for information.
        Note: Requires external search API integration (e.g., Google Custom Search, DuckDuckGo)
        This is a placeholder implementation.
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Search API key not configured. Set SEARCH_API_KEY environment variable.",
                "results": [],
            }
        
        # Placeholder: In production, integrate with actual search APIs
        # Example: Google Custom Search, SerpAPI, or DuckDuckGo API
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "title": "Search result placeholder",
                    "url": "https://example.com",
                    "snippet": "This is a placeholder. Configure a real search API for production.",
                }
            ],
            "count": 1,
        }
    
    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch and extract content from a URL"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                # Extract text content (simplified - in production use BeautifulSoup or similar)
                content = response.text[:5000]  # Limit content length
                
                return {
                    "success": True,
                    "url": url,
                    "status_code": response.status_code,
                    "content": content,
                    "content_length": len(response.text),
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None,
            }
