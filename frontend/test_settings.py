import sys
sys.path.insert(0, 'D:/Code/Folder Steward/backend')
import os
os.environ['FS_DATABASE_PATH'] = 'C:/Users/lu/AppData/Roaming/folder-steward-frontend/folder_steward.db'
from app.services.llm_provider_service import LLMProviderService
s = LLMProviderService()
print(s._get_settings())
