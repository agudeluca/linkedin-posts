import logging
import requests
import json
from typing import Dict, List
from filters.message_filters import MessageFilter

def extract_json_from_response(llm_output: str):
    first_brace = llm_output.find("{")
    last_brace = llm_output.rfind("}")
    
    if first_brace != -1 and last_brace != -1:
        llm_formatted_json = llm_output[first_brace:last_brace + 1]
        try:
            return json.loads(llm_formatted_json)  # Ensure it's valid JSON
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from extracted response")
            return {}
    
    logging.error("No valid JSON found in response")
    return {}

def get_formatted_prompt(raw_text: str):
    PROMPT = """Organize the following text using the following json format. 

    Constraints:
    0. Only return the json with no additional text.
    
    1. If no relevant information for a field is found, leave it blank
    2. languages should be a list of available programming languages
    3. summarize the job_description to 255 characters
    4. salary should be accompanied with the currency (USD, ARS, EUR). Example "1000 ARS", "1000 USD"
    5. remote should only contain one of the following values: "full", "hybrid", or "office". Leave it blank if no value can be derived from the text.. Leave blank if no value can be derived from the text.
    6. locations should include the work location, like "Argentina" or "Buenos Aires, Argentina" or "Capital Federal, Argentina"
    7. Only return the json with no additional text.

    Json format: [{"company_name": "", "languages": [], "job_description": "", "required_experience": "", "salary": "", "remote": "full|hybrid|office", "locations": []}]

    {raw_text}
    """
    return PROMPT.format(raw_text=raw_text)

class DeepSeekAIFormatter(MessageFilter):
    def __init__(self, deepseek_api_url: str, deepseek_api_token: str):
        self.deepseek_api_url = deepseek_api_url
        self.deepseek_api_token = deepseek_api_token
    
    logger = logging.getLogger(__name__)

    def apply_to_messages(self, messages: List[Dict]) -> List[Dict]:
        formatted_response = []
        for message in messages:
            content = message.get("content")
            if content:
                formatted_content = self.send_to_llm(content)
                message["deepseek_formatted_content"] = formatted_content
            else:
                self.logger.warning("Skipping message with missing content")
            formatted_response.append(message)
        return formatted_response

    def send_to_llm(self, raw_text: str)  -> List[Dict]:
        formatted_prompt = get_formatted_prompt(raw_text)
        
        try:
            response = requests.post(
                self.deepseek_api_url,
                headers={"Authorization": f"Bearer {self.deepseek_api_token}", "Content-Type": "application/json"},
                json={"prompt": formatted_prompt, "max_tokens": 500}
            )
            
            if response.status_code == 200:
                return extract_json_from_response(response.text.strip())
            else:
                self.logger.error(f"Unexpected response code {response.status_code}: {response.text}")
        except requests.RequestException as e:
            self.logger.error(f"Error calling DeepSeekAI API: {e}")
        
        return []

class OpenAIFormatter(MessageFilter):
    def __init__(self, openai_api_url: str, openai_api_token: str):
        self.openai_api_url = openai_api_url
        self.openai_api_token = openai_api_token
    
    logger = logging.getLogger(__name__)

    def apply_to_messages(self, messages: List[Dict]) -> List[Dict]:
        formatted_response = []
        for message in messages:
            content = message.get("content")
            if content:
                formatted_content = self.send_to_openai(content)
                message["openai_formatted_content"] = formatted_content
            else:
                self.logger.warning("Skipping message with missing content")
            formatted_response.append(message)
        return formatted_response

    def send_to_llm(self, raw_text: str) -> List[Dict]:
        formatted_prompt = get_formatted_prompt(raw_text)

        try:
            response = requests.post(
                self.openai_api_url,
                headers={"Authorization": f"Bearer {self.openai_api_token}", "Content-Type": "application/json"},
                json={"prompt": formatted_prompt, "max_tokens": 500}
            )
            
            if response.status_code == 200:
                return extract_json_from_response(response.text.strip())
            else:
                self.logger.error(f"Unexpected response code {response.status_code}: {response.text}")
        except requests.RequestException as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
        
        return []
