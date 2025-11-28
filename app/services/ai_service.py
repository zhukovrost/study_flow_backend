"""
Сервис для работы с GigaChat для разбиения задач на подзадачи
"""
import json
import logging
import requests
import base64
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GigaChatAuth:
    """Класс для управления авторизацией GigaChat"""
    
    def __init__(self, client_id: str, client_secret: str, oauth_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_url = oauth_url
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def _get_authorization_key(self) -> str:
        """Получить Authorization key для Basic-аутентификации"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded}"
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Получить актуальный Access token
        
        Args:
            force_refresh: Принудительно обновить токен
        
        Returns:
            Access token
        """
        # Проверяем, есть ли валидный токен
        if not force_refresh and self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=2):  # Обновляем за 2 минуты до истечения
                return self.access_token
        
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': f'{int(time.time() * 1000)}',  # Уникальный идентификатор запроса
                'Authorization': self._get_authorization_key()
            }
            
            payload = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            logger.debug("Запрос Access token от GigaChat")
            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=payload,
                timeout=10,
                verify=True  # В проде лучше использовать доверенный сертификат
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get('access_token')
            # expires_at может быть в секундах (unix timestamp) или в формате строки
            # Если не указано, используем 30 минут по умолчанию
            expires_at = token_data.get('expires_at')
            if expires_at:
                # Если это число (unix timestamp в секундах)
                if isinstance(expires_at, (int, float)):
                    self.token_expires_at = datetime.fromtimestamp(expires_at)
                else:
                    # Если это строка, пытаемся распарсить
                    try:
                        self.token_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    except:
                        # Если не получилось, используем 30 минут
                        self.token_expires_at = datetime.now() + timedelta(seconds=1800)
            else:
                # Если expires_at не указан, используем expires_in (если есть) или 30 минут
                expires_in = token_data.get('expires_in', 1800)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            if not self.access_token:
                raise Exception("Access token не получен в ответе")
            
            logger.debug("Access token успешно получен")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка при получении Access token: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nДетали: {error_detail}"
                except:
                    error_msg += f"\nСтатус: {e.response.status_code}, Текст: {e.response.text[:200]}"
            logger.error(error_msg)
            raise Exception(f"Не удалось получить Access token: {e}")


class TaskBreakdownService:
    """Сервис для разбиения задач на подзадачи с помощью GigaChat"""
    
    def __init__(self, client_id: str, client_secret: str, model_name: str = "GigaChat", 
                 oauth_url: str = None, api_url: str = None):
        """
        Инициализация сервиса
        
        Args:
            client_id: CLIENT_ID из кабинета Сбера
            client_secret: CLIENT_SECRET из кабинета Сбера
            model_name: Название модели (по умолчанию GigaChat)
            oauth_url: URL для OAuth (опционально)
            api_url: URL для Chat Completions API (опционально)
        """
        from app.core.config import settings
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.model_name = model_name
        self.oauth_url = oauth_url or settings.GIGACHAT_OAUTH_URL
        self.api_url = api_url or settings.GIGACHAT_API_URL
        
        # Инициализируем авторизацию
        self.auth = GigaChatAuth(self.client_id, self.client_secret, self.oauth_url)
        
        # Системный промпт для строгого JSON
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
      "dependencies": ["<id других подзадач>"]
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
        # Формируем пользовательский промпт
        user_prompt = f'Разбей на подзадачи: "{task_description}"'
        
        if context:
            user_prompt += f"\nКонтекст: {context}"
        
        if constraints:
            user_prompt += f"\nОграничения: {constraints}"
        
        response_text: str = ""
        try:
            # Получаем актуальный Access token
            access_token = self.auth.get_access_token()
            
            # Подготавливаем запрос к GigaChat API
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.6,
                "max_tokens": 2000
            }
            
            # Отправляем запрос в GigaChat API
            logger.debug(f"Отправка запроса к GigaChat: {self.model_name}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=True  # В проде лучше использовать доверенный сертификат
            )
            
            # Если получили 401, пробуем обновить токен и повторить запрос
            if response.status_code == 401:
                logger.warning("Получен 401, обновляем токен и повторяем запрос")
                access_token = self.auth.get_access_token(force_refresh=True)
                headers['Authorization'] = f'Bearer {access_token}'
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                    verify=True
                )
            
            # Проверяем статус ответа
            response.raise_for_status()
            response_data = response.json()
            
            # Извлекаем текст ответа из структуры GigaChat
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    response_text = choice["message"]["content"].strip()
                else:
                    raise Exception("Неожиданная структура ответа: отсутствует message.content")
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
            error_msg = f"Ошибка HTTP запроса к GigaChat: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nДетали: {error_detail}"
                except:
                    error_msg += f"\nСтатус: {e.response.status_code}, Текст: {e.response.text[:200]}"
            logger.error(error_msg)
            raise Exception(f"Ошибка при обращении к GigaChat API: {e}")
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON: {e}"
            if response_text:
                error_msg += f"\nОтвет: {response_text[:500]}"
            logger.error(error_msg)
            raise ValueError(f"Не удалось разобрать ответ от AI как JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обращении к GigaChat: {e}")
            raise Exception(f"Ошибка при обращении к AI сервису: {e}")


def create_task_breakdown_service(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Optional[TaskBreakdownService]:
    """
    Создать экземпляр сервиса разбиения задач
    
    Args:
        client_id: CLIENT_ID (если не указан, берется из настроек)
        client_secret: CLIENT_SECRET (если не указан, берется из настроек)
    
    Returns:
        Экземпляр сервиса или None, если учетные данные не настроены
    """
    from app.core.config import settings
    
    if client_id is None:
        client_id = getattr(settings, 'GIGACHAT_CLIENT_ID', None)
    
    if client_secret is None:
        client_secret = getattr(settings, 'GIGACHAT_CLIENT_SECRET', None)
    
    if not client_id:
        logger.warning("GigaChat CLIENT_ID не настроен. Функция разбиения задач недоступна.")
        return None
    
    if not client_secret:
        logger.warning("GigaChat CLIENT_SECRET не настроен. Функция разбиения задач недоступна.")
        return None
    
    model_name = getattr(settings, 'GIGACHAT_MODEL', 'GigaChat')
    
    return TaskBreakdownService(
        client_id=client_id,
        client_secret=client_secret,
        model_name=model_name
    )
