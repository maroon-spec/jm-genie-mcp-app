"""
Genie MCP Client
Databricks Genie MCPサーバーとの通信を行うクライアントクラス
"""

import json
import requests
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MCPRequest:
    """MCPリクエストのデータクラス"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.params is None:
            self.params = {}


@dataclass
class MCPResponse:
    """MCPレスポンスのデータクラス"""
    jsonrpc: str = "2.0"
    id: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class GenieMCPClient:
    """Genie MCPサーバーとの通信を行うクライアントクラス"""
    
    def __init__(self, workspace_hostname: str, genie_space_id: str, access_token: str):
        """
        Genie MCPクライアントを初期化
        
        Args:
            workspace_hostname: Databricksワークスペースのホスト名
            genie_space_id: GenieスペースのID
            access_token: アクセストークン
        """
        # workspace_hostnameからhttps://プレフィックスを除去
        if workspace_hostname.startswith('https://'):
            workspace_hostname = workspace_hostname[8:]  # 'https://'を除去
        elif workspace_hostname.startswith('http://'):
            workspace_hostname = workspace_hostname[7:]  # 'http://'を除去
            
        self.base_url = f"https://{workspace_hostname}/api/2.0/mcp/genie/{genie_space_id}"
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, request: MCPRequest) -> MCPResponse:
        """
        MCPリクエストを送信
        
        Args:
            request: MCPリクエストオブジェクト
            
        Returns:
            MCPレスポンスオブジェクト
        """
        try:
            response = self.session.post(
                self.base_url,
                json=request.__dict__,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return MCPResponse(**data)
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": response.status_code,
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
                )
                
        except requests.exceptions.Timeout:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -1,
                    "message": "Request timeout"
                }
            )
        except requests.exceptions.RequestException as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -1,
                    "message": f"Request failed: {str(e)}"
                }
            )
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -1,
                    "message": f"Unexpected error: {str(e)}"
                }
            )
    
    def initialize(self) -> MCPResponse:
        """
        MCPサーバーとの初期化
        
        Returns:
            MCPレスポンスオブジェクト
        """
        request = MCPRequest(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "genie-mcp-client",
                    "version": "1.0.0"
                }
            }
        )
        return self._make_request(request)
    
    def query_genie(self, question: str) -> MCPResponse:
        """
        Genieスペースに対して質問を送信
        
        Args:
            question: 質問内容
            
        Returns:
            MCPレスポンスオブジェクト
        """
        request = MCPRequest(
            method="tools/call",
            params={
                "name": "query_space_01efbd0fe8711ecd80e48dcbc4042f28",
                "arguments": {
                    "query": question
                }
            }
        )
        return self._make_request(request)
    
    def close(self):
        """セッションを閉じる"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class GenieMCPResponseParser:
    """Genie MCPレスポンスを解析するクラス"""
    
    @staticmethod
    def parse_response(response: MCPResponse) -> Dict[str, Any]:
        """
        MCPレスポンスを解析
        
        Args:
            response: MCPレスポンスオブジェクト
            
        Returns:
            解析された結果辞書
        """
        if response.error:
            return {
                "success": False,
                "error": response.error,
                "data": None
            }
        
        if response.result:
            return {
                "success": True,
                "error": None,
                "data": response.result,
                "content": response.result.get("content", ""),
                "metadata": response.result.get("metadata", {})
            }
        
        return {
            "success": False,
            "error": {"message": "No result or error in response"},
            "data": None
        }
    
    @staticmethod
    def extract_text_content(response: MCPResponse) -> str:
        """
        レスポンスからテキストコンテンツを抽出
        
        Args:
            response: MCPレスポンスオブジェクト
            
        Returns:
            テキストコンテンツ
        """
        if response.result and "content" in response.result:
            content = response.result["content"]
            if isinstance(content, str):
                return content
            elif isinstance(content, dict):
                return content.get("text", "")
            elif isinstance(content, list):
                # 複数のコンテンツがある場合、テキストを結合
                texts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                return " ".join(texts)
        return ""
    
    @staticmethod
    def extract_dataframe(response: MCPResponse) -> Optional[Dict[str, Any]]:
        """
        レスポンスからデータフレーム情報を抽出
        
        Args:
            response: MCPレスポンスオブジェクト
            
        Returns:
            データフレーム情報辞書
        """
        if response.result and "data" in response.result:
            return response.result["data"]
        return None 
    