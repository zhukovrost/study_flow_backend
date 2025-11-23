"""
Сервис для работы с YandexGPT для разбиения задач на подзадачи
"""
import json
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# YandexGPT API endpoint
YANDEXGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


class TaskBreakdownService:
    """Сервис для разбиения задач на подзадачи с помощью YandexGPT"""
    
    def __init__(self, api_key: str, folder_id: str, model_name: str = "yandexgpt-5.1"):
        """
        Инициализация сервиса
        
        Args:
            api_key: API ключ для Yandex Cloud (IAM токен или API ключ)
            folder_id: ID каталога в Yandex Cloud
            model_name: Название модели (по умолчанию yandexgpt-5.1)
        """
        self.api_key = api_key
        self.folder_id = folder_id
        self.model_name = model_name
        
        # Системный промпт
        self.system_prompt = """Ты — помощник-планировщик. Твоя задача: принимать одну входную задачу на естественном языке и разбивать её на 3–5 подзадач. 

Требования к ответу:

1) Строго верни валидный JSON UTF-8 без пояснений/текста вокруг.

2) Поля и типы:

{
  "version": "v1",
  "input_task": "<строка>",
  "subtasks": [
    {
      "id": "<s1|s2|...>",
      "title": "<краткий заголовок>",
      "description": "<что сделать, 1–3 предложения>",
      "acceptance_criteria": ["<проверяемые критерии>", "..."],
      "priority": "<high|medium|low>",
      "estimated_effort": <целое от 1 до 5>, 
      "dependencies": ["<id других подзадач>"]  // может быть []
    }
  ]
}

3) Всегда 3–5 осмысленных подзадач. Не выдумывай лишних внешних требований. 

4) Не добавляй комментарии, пояснения, Markdown или код — только JSON."""

    def break_down_task(
        self, 
        task_description: str,
        context: Optional[str] = None,
        constraints: Optional[str] = None
    ) -> Dict:
        """
        Разбить задачу на подзадачи
        
        Args:
            task_description: Описание задачи на естественном языке
            context: Необязательный контекст
            constraints: Необязательные ограничения (дедлайны/технологии/ресурсы)
        
        Returns:
            Словарь с разбиением задачи на подзадачи
        
        Raises:
            ValueError: Если не удалось разобрать ответ от AI
            Exception: Если произошла ошибка при обращении к API
        """
        # Формируем запрос
        user_prompt = f'Разбей на подзадачи: "{task_description}"'
        
        if context:
            user_prompt += f"\nКонтекст: {context}"
        
        if constraints:
            user_prompt += f"\nОграничения: {constraints}"
        
        # Формируем полный промпт
        full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
        
        response_text: str = ""
        try:
            # Подготавливаем запрос к YandexGPT API
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "modelUri": f"gpt://{self.folder_id}/{self.model_name}",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.6,
                    "maxTokens": 2000
                },
                "messages": [
                    {
                        "role": "user",
                        "text": full_prompt
                    }
                ]
            }
            
            # Отправляем запрос в YandexGPT API
            logger.debug(f"Отправка запроса к YandexGPT: {self.model_name}")
            response = requests.post(
                YANDEXGPT_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Проверяем статус ответа
            response.raise_for_status()
            response_data = response.json()
            
            # Извлекаем текст ответа
            if "result" in response_data and "alternatives" in response_data["result"]:
                if len(response_data["result"]["alternatives"]) > 0:
                    response_text = response_data["result"]["alternatives"][0]["message"]["text"].strip()
                else:
                    raise Exception("Пустой ответ от YandexGPT API")
            else:
                raise Exception(f"Неожиданная структура ответа: {response_data}")
            
            # Убираем markdown код блоки, если есть
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Парсим JSON
            result = json.loads(response_text)
            
            # Валидация структуры
            if "subtasks" not in result or not isinstance(result["subtasks"], list):
                raise ValueError("Некорректная структура ответа: отсутствует поле 'subtasks'")
            
            if len(result["subtasks"]) < 3 or len(result["subtasks"]) > 5:
                logger.warning(f"Получено {len(result['subtasks'])} подзадач, ожидалось 3-5")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка HTTP запроса к YandexGPT: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nДетали: {error_detail}"
                except:
                    error_msg += f"\nСтатус: {e.response.status_code}, Текст: {e.response.text[:200]}"
            logger.error(error_msg)
            raise Exception(f"Ошибка при обращении к YandexGPT API: {e}")
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON: {e}"
            if response_text:
                error_msg += f"\nОтвет: {response_text[:500]}"
            logger.error(error_msg)
            raise ValueError(f"Не удалось разобрать ответ от AI как JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обращении к YandexGPT: {e}")
            raise Exception(f"Ошибка при обращении к AI сервису: {e}")


def create_task_breakdown_service(
    api_key: Optional[str] = None,
    folder_id: Optional[str] = None
) -> Optional[TaskBreakdownService]:
    """
    Создать экземпляр сервиса разбиения задач
    
    Args:
        api_key: API ключ (если не указан, берется из настроек)
        folder_id: ID каталога (если не указан, берется из настроек)
    
    Returns:
        Экземпляр сервиса или None, если API ключ не настроен
    """
    from app.core.config import settings
    
    if api_key is None:
        # Пытаемся получить из настроек
        api_key = getattr(settings, 'YANDEXGPT_API_KEY', None)
    
    if folder_id is None:
        folder_id = getattr(settings, 'YANDEXGPT_FOLDER_ID', None)
    
    if not api_key:
        logger.warning("YandexGPT API ключ не настроен. Функция разбиения задач недоступна.")
        return None
    
    if not folder_id:
        logger.warning("YandexGPT Folder ID не настроен. Функция разбиения задач недоступна.")
        return None
    
    model_name = getattr(settings, 'YANDEXGPT_MODEL', 'yandexgpt-5.1')
    
    return TaskBreakdownService(api_key=api_key, folder_id=folder_id, model_name=model_name)
