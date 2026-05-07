import sys
sys.path.insert(0, 'D:/Code/Folder Steward/backend')
from app.services.llm_provider_service import LLMProviderService
s = LLMProviderService()
print(s.generate_classification({'filename':'test'}, [], 'D:/Archive'))
