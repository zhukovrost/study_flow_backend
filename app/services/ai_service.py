"""
Сервис для работы с Google AI (Gemini) для разбиения задач на подзадачи
"""
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai  # type: ignore
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore
    GOOGLE_AI_AVAILABLE = False
    logger.warning("google-generativeai не установлен. Установите: pip install google-generativeai")


class TaskBreakdownService:
    """Сервис для разбиения задач на подзадачи с помощью Google AI"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Инициализация сервиса
        
        Args:
            api_key: API ключ для Google AI
            model_name: Название модели (по умолчанию gemini-pro)
        """
        if not GOOGLE_AI_AVAILABLE or genai is None:
            raise ImportError("google-generativeai не установлен. Установите: pip install google-generativeai")
        
        genai.configure(api_key=api_key)  # type: ignore
        self.model = genai.GenerativeModel(model_name)  # type: ignore
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
        
        response_text: str = ""
        try:
            # Формируем полный промпт
            full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
            
            # Отправляем запрос в Google AI
            response = self.model.generate_content(full_prompt)  # type: ignore
            
            # Извлекаем текст ответа
            response_text = response.text.strip()  # type: ignore
            
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
            
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON: {e}"
            if response_text:
                error_msg += f"\nОтвет: {response_text[:500]}"
            logger.error(error_msg)
            raise ValueError(f"Не удалось разобрать ответ от AI как JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обращении к Google AI: {e}")
            raise Exception(f"Ошибка при обращении к AI сервису: {e}")


def create_task_breakdown_service(api_key: Optional[str] = None) -> Optional[TaskBreakdownService]:
    """
    Создать экземпляр сервиса разбиения задач
    
    Args:
        api_key: API ключ (если не указан, берется из настроек)
    
    Returns:
        Экземпляр сервиса или None, если API ключ не настроен
    """
    from app.core.config import settings
    
    if api_key is None:
        # Пытаемся получить из настроек
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
    
    if not api_key:
        logger.warning("Google AI API ключ не настроен. Функция разбиения задач недоступна.")
        return None
    
    model_name = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-pro')
    
    return TaskBreakdownService(api_key=api_key, model_name=model_name)

