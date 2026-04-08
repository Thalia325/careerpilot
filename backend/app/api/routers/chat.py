import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routers.apikey import get_user_api_keys
from app.core.config import get_settings
from app.integrations.llm.providers import ErnieLLMProvider
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()

SYSTEM_PROMPT = (
    "你是职航智策（CareerPilot）的职业规划AI助手，专门帮助中国大学生分析职业方向、岗位匹配、能力评估和职业路径规划。"
    "请用中文回答，回答要简洁实用，每次回复不超过500字。"
    "如果用户的问题与职业规划无关，礼貌地引导回职业话题。"
)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ChatResponse:
    keys = get_user_api_keys(db, current_user.id)
    if not keys:
        return ChatResponse(reply="请先在侧边栏的「AI 模型设置」中配置你的文心一言 API Key，配置后即可开始对话。")

    settings = get_settings()
    provider = ErnieLLMProvider(
        api_key=keys.api_key,
        secret_key=keys.secret_key,
        base_url=settings.ernie_base_url,
        aistudio_base_url=settings.ernie_aistudio_base_url,
        model=settings.ernie_model,
        auth_mode=keys.auth_mode,
    )
    try:
        reply = provider._chat(SYSTEM_PROMPT, payload.message)
        return ChatResponse(reply=reply)
    except ValueError as exc:
        return ChatResponse(reply=f"API 认证失败：{exc}。请在「AI 模型设置」中检查密钥配置。")
    except ConnectionError:
        return ChatResponse(reply="网络连接失败，无法连接到 AI 服务，请检查网络后重试。")
    except TimeoutError:
        return ChatResponse(reply="请求超时，AI 服务响应较慢，请稍后再试。")
    except Exception as exc:
        logger.warning("Chat failed for user %s: %s", current_user.id, exc)
        return ChatResponse(reply=f"AI 模型调用失败：{exc}。请检查密钥配置或稍后再试。")
