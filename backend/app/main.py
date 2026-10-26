import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.sessions import SessionMiddleware

from app import ai, config, db
from app.board import Board
from app.chat import (
    AIResponse,
    ChatRequest,
    apply_operations,
    build_messages,
    correction_messages,
)
from app.security import RateLimiter, client_ip, content_security_policy, credentials_valid

STATIC_DIR = os.environ.get(
    "STATIC_DIR", Path(__file__).parents[2] / "frontend" / "out"
)

logger = logging.getLogger(__name__)
# uvicorn only configures its own loggers, so without this the app's INFO logs are dropped.
logging.basicConfig(level=logging.INFO)

# Failed sign-ins per client IP, and chat requests (each one or two AI calls) per user.
login_limiter = RateLimiter(limit=5, window=15 * 60)
chat_limiter = RateLimiter(limit=20, window=60 * 60)

SECURITY_HEADERS = {
    "Content-Security-Policy": content_security_policy(STATIC_DIR),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db(config.APP_USERNAME)
    yield


# The API docs are only served in development.
no_docs = {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(lifespan=lifespan, **(no_docs if config.PRODUCTION else {}))
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    max_age=7 * 24 * 60 * 60,
    same_site="lax",
    # Secure cookies need HTTPS, which Render provides and local Docker doesn't.
    https_only=config.PRODUCTION,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    # Swagger UI and ReDoc (development only) load their scripts from a CDN.
    if request.url.path in ("/docs", "/redoc"):
        del response.headers["Content-Security-Policy"]
    return response


class Credentials(BaseModel):
    # Capped so that huge passwords can't make hashing expensive.
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)


class ChatResponse(BaseModel):
    reply: str
    board: Board | None


def current_user(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not signed in")
    return username


def current_user_id(username: str = Depends(current_user)) -> int:
    return db.get_user_id(username)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(credentials: Credentials, request: Request):
    ip = client_ip(request)
    if login_limiter.is_limited(ip):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts, try again later")
    if not credentials_valid(credentials.username, credentials.password):
        login_limiter.hit(ip)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session.clear()
    request.session["username"] = config.APP_USERNAME
    return {"username": config.APP_USERNAME}


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}


@app.get("/api/me")
def me(username: str = Depends(current_user)):
    return {"username": username}


@app.get("/api/board")
def read_board(user_id: int = Depends(current_user_id)) -> Board:
    return db.get_board(user_id)


@app.put("/api/board")
def update_board(board: Board, user_id: int = Depends(current_user_id)) -> Board:
    db.save_board(user_id, board)
    return board


@app.post("/api/chat")
def chat(request: ChatRequest, user_id: int = Depends(current_user_id)) -> ChatResponse:
    if chat_limiter.is_limited(user_id):
        raise HTTPException(status_code=429, detail="Chat limit reached, try again later")
    chat_limiter.hit(user_id)
    board = db.get_board(user_id)
    messages = build_messages(board, request)
    # The first attempt, then one retry where the model sees the error and corrects itself.
    for attempt in range(2):
        try:
            response = ai.parse(messages, AIResponse)
        except (OpenAIError, ValidationError) as error:
            # e.g. OpenRouter is down, the reply was cut off at MAX_TOKENS, or it isn't valid JSON.
            logger.warning("AI call failed: %r", error)
            raise HTTPException(status_code=502, detail="The AI call failed")
        logger.info(
            "AI operations on attempt %d: %s",
            attempt + 1,
            [operation.model_dump() for operation in response.operations],
        )
        try:
            updated = apply_operations(board, response.operations)
            break
        except ValueError as error:
            logger.warning("Rejected AI operations on attempt %d: %s", attempt + 1, error)
            if attempt == 1:
                raise HTTPException(status_code=502, detail="The AI returned an invalid update")
            messages += correction_messages(response, error)
    if not response.operations:
        return ChatResponse(reply=response.reply, board=None)
    db.save_board(user_id, updated)
    return ChatResponse(reply=response.reply, board=updated)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
