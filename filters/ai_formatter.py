import logging
import requests
import json
from typing import Dict, List, overload
from filters.message_filters import MessageFilter

def extract_json_from_response(llm_output: str):
    logging.debug(f"LLM raw output - {llm_output}")

    first_brace = llm_output.find("[")
    last_brace = llm_output.rfind("]")
    
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
    PROMPT = r"""Organize the following text using the following json format. 

    Constraints:
    0. Only return the json with no additional text.
    1. If no relevant information for a field is found, leave it blank
    2. programming_languages should be a list of requested programming languages
    3. summarize the job_description to 255 characters
    4. salary should be accompanied with the currency (USD, ARS, EUR). Example "1000 ARS", "1000 USD"
    5. remote should only contain one of the following values: fully_remote hybrid_work office_work. Leave it blank if no value can be derived from the text.
    6. locations should include the work location, like "Argentina" or "Buenos Aires, Argentina" or "Capital Federal, Argentina"
    7. minimum_experience should be an integer representing the number of years. Leave it blank if no value can be derived from the text.
    8. salary currency should only be ARS, USD or EUR. Leave it blank if no value can be derived from the text.
    9. salary should be an integer. salary should ONLY contain numbers. Leave it blank if no value can be derived from the text.
    10. Only return the json with no additional text.

    Json format: [{"company_name": "", "programming_languages": [], "job_description": "", "minimum_experience": "5", "salary": "","salary_currency": "USD|ARS|EUR", "remote": "fully_remote|hybrid_work|office_work", "locations": []}]

    text to organize below this line

    """
    return PROMPT + raw_text

class DeepSeekAIFormatter(MessageFilter):
    def __init__(self, api_url: str, api_token: str, *args, **kwargs):
        self.api_url = api_url
        self.api_token = api_token
    
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
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"},
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

    _MODEL = "gpt-3.5-turbo"

    def __init__(self, api_url: str, api_token: str, *args, **kwargs):
        self.api_url = api_url
        self.api_token = api_token
        self.openai_project_id = kwargs.get("openai_project_id")
        self.openai_org_id = kwargs.get("openai_org_id")

    logger = logging.getLogger(__name__)

    def apply_to_messages(self, messages: List[Dict]) -> List[Dict]:
        formatted_response = []
        for message in messages:
            content = message.get("content")
            if content:
                formatted_content = self.send_to_llm(content)
                message["openai_formatted_content"] = formatted_content
            else:
                self.logger.warning("Skipping message with missing content")
            formatted_response.append(message)
        return formatted_response

    def send_to_llm(self, raw_text: str) -> List[Dict]:
        formatted_prompt = get_formatted_prompt(raw_text)

        try:
            llm_configure_prompt = {
                "model": self._MODEL,
                "messages": [{"role": "user", "content": formatted_prompt}],
                "temperature": 1.0
            }
            service_path = "chat/completions"
            response = requests.post(
                f"{self.api_url}/{service_path}",
                headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json", "OpenAI-Project": self.openai_project_id, "OpenAI-Organization": self.openai_org_id},
                json=llm_configure_prompt
            )
            if response.status_code == 200:
                response_json = response.json()
                if response_json["choices"]:
                    response_json_message: str = response_json["choices"][0]["message"]["content"]
                    return extract_json_from_response(response_json_message.strip())
            else:
                self.logger.error(f"Unexpected response code {response.status_code}: {response.text}")
        except requests.RequestException as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
        
        return []
