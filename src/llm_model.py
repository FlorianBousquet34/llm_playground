from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.settings import ModelSettings
from pydantic_ai.messages import ModelResponse, ModelMessage, TextPart

from llm_loader import call_llm_model

class LocalLLMModel(Model):
    
    model_name : str
    
    def __init__(self, model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"):
        self.model_name = model_name
        
    def model_name(self):
        return self.model_name
    
    async def request(self,
                      messages: list[ModelMessage],
                      model_settings: ModelSettings | None,
                      model_request_parameters: ModelRequestParameters) -> ModelResponse:
        user_messages, system_messages = [], []
        for msg in messages:
            for part in msg.parts:
                if part.part_kind == 'system-prompt':
                    system_messages.append(part.content)
                elif part.part_kind == 'user-prompt':
                    user_messages.append(part.content)
        resp = call_llm_model(user_messages, system_messages, self.model_name)
        return ModelResponse([TextPart(resp)], model_name=self.model_name)
    
    
    def system(self):
        return "local_llm"