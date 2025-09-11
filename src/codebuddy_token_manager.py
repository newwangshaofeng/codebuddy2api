"""
CodeBuddy Token Manager - 管理CodeBuddy认证token
"""
import os
import glob
import json
import time
import logging
from typing import Dict, Optional, List
from .usage_stats_manager import usage_stats_manager

logger = logging.getLogger(__name__)


class CodeBuddyTokenManager:
    """CodeBuddy Token管理器"""
    
    def __init__(self, creds_dir=None):
        if creds_dir is None:
            from config import get_codebuddy_creds_dir, get_rotation_count
            creds_dir = get_codebuddy_creds_dir()
        
        self.creds_dir = os.path.join(os.path.dirname(__file__), '..', creds_dir)
        self.credentials = []
        self.current_index = 0  # Start from the first credential
        self.usage_count = 0    # Counter for the current credential usage
        self.manual_selected_index = None  # 手动选择的凭证索引
        self.load_all_tokens()
    
    def load_all_tokens(self):
        """加载所有token文件"""
        self.credentials = []
        self.current_index = -1
        
        logger.info(f"Loading CodeBuddy credentials from: {self.creds_dir}")
        
        if not os.path.exists(self.creds_dir):
            os.makedirs(self.creds_dir)
            logger.warning(f"Credentials directory created at {self.creds_dir}. No credentials found.")
            return
        
        token_files = glob.glob(os.path.join(self.creds_dir, '*.json'))
        for file_path in token_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'bearer_token' in data:
                        self.credentials.append({
                            'file_path': file_path,
                            'data': data
                        })
                        logger.info(f"Successfully loaded credential: {os.path.basename(file_path)}")
                    else:
                        logger.warning(f"Skipping invalid credential file (missing bearer_token): {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Failed to load credential file {os.path.basename(file_path)}: {e}")
        
        logger.info(f"Loaded a total of {len(self.credentials)} CodeBuddy credentials.")
    
    def get_next_credential(self) -> Optional[Dict]:
        """获取下一个可用的凭证，根据轮换策略"""
        from config import get_rotation_count

        if not self.credentials:
            return None
        
        # 如果当前索引无效（例如，在加载后删除了所有凭证），则重置
        if self.current_index >= len(self.credentials):
            self.current_index = 0
            self.usage_count = 0

        rotation_count = get_rotation_count()
        
        # 如果有手动选择的凭证，优先使用
        if self.manual_selected_index is not None and 0 <= self.manual_selected_index < len(self.credentials):
            credential = self.credentials[self.manual_selected_index]
            credential_filename = os.path.basename(credential['file_path'])
            usage_stats_manager.record_credential_usage(credential_filename)
            logger.info(f"Using manually selected credential: {credential_filename}")
            return credential['data']
        
        # 如果轮换次数设置为0，关闭轮换，只使用当前凭证
        if rotation_count == 0:
            credential = self.credentials[self.current_index]
            credential_filename = os.path.basename(credential['file_path'])
            usage_stats_manager.record_credential_usage(credential_filename)
            logger.info(f"Using fixed credential (rotation disabled): {credential_filename}")
            return credential['data']

        # 正常轮换逻辑
        if self.usage_count >= rotation_count:
            self.current_index = (self.current_index + 1) % len(self.credentials)
            self.usage_count = 0  # 重置计数器
            logger.info("Credential rotation triggered.")

        credential = self.credentials[self.current_index]
        self.usage_count += 1
        
        # Record usage stats
        credential_filename = os.path.basename(credential['file_path'])
        usage_stats_manager.record_credential_usage(credential_filename)
        
        logger.info(
            f"Using credential: {credential_filename} "
            f"(Usage: {self.usage_count}/{rotation_count})"
        )
        return credential['data']
    
    def get_all_credentials(self) -> List[Dict]:
        """获取所有凭证"""
        return [cred['data'] for cred in self.credentials]
    
    def add_credential(self, bearer_token: str, user_id: str = None, filename: str = None) -> bool:
        """添加新的凭证"""
        if not filename:
            filename = f"codebuddy_token_{len(self.credentials) + 1}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = os.path.join(self.creds_dir, filename)
        
        credential_data = {
            "bearer_token": bearer_token,
            "user_id": user_id,
            "created_at": int(time.time())
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(credential_data, f, indent=4)
            
            logger.info(f"Added new credential: {filename}")
            self.load_all_tokens()  # 重新加载
            return True
        except Exception as e:
            logger.error(f"Failed to save credential: {e}")
            return False
    
    def set_manual_credential(self, index: int) -> bool:
        """手动选择指定索引的凭证"""
        if 0 <= index < len(self.credentials):
            self.manual_selected_index = index
            credential_filename = os.path.basename(self.credentials[index]['file_path'])
            logger.info(f"Manually selected credential: {credential_filename} (index: {index})")
            return True
        else:
            logger.error(f"Invalid credential index: {index}")
            return False
    
    def clear_manual_selection(self):
        """清除手动选择，恢复自动轮换"""
        self.manual_selected_index = None
        logger.info("Cleared manual credential selection, resumed automatic rotation")
    
    def get_current_credential_info(self) -> Dict:
        """获取当前使用的凭证信息"""
        from config import get_rotation_count
        
        if not self.credentials:
            return {"status": "no_credentials"}
        
        rotation_count = get_rotation_count()
        
        if self.manual_selected_index is not None:
            credential = self.credentials[self.manual_selected_index]
            return {
                "status": "manual_selected",
                "index": self.manual_selected_index,
                "filename": os.path.basename(credential['file_path']),
                "user_id": credential['data'].get('user_id', 'unknown')
            }
        elif rotation_count == 0:
            credential = self.credentials[self.current_index]
            return {
                "status": "rotation_disabled",
                "index": self.current_index,
                "filename": os.path.basename(credential['file_path']),
                "user_id": credential['data'].get('user_id', 'unknown')
            }
        else:
            credential = self.credentials[self.current_index]
            return {
                "status": "auto_rotation",
                "index": self.current_index,
                "filename": os.path.basename(credential['file_path']),
                "user_id": credential['data'].get('user_id', 'unknown'),
                "usage_count": self.usage_count,
                "rotation_count": rotation_count
            }


# 全局token管理器实例
codebuddy_token_manager = CodeBuddyTokenManager()