import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app import ai, db
from app.board import Board
from app.chat import AIResponse, ChatRequest, apply_operations, build_messages

STATIC_DIR = os.environ.get(
    "STATIC_DIR", Path(__file__).parents[2] / "frontend" / "out"
)
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret")

logger = logging.getLogger(__name__)

# Hardcoded for the MVP.
USERNAME = "user"
PASSWORD = "password"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db(USERNAME)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


class Credentials(BaseModel):
    username: str
    password: str


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
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["username"] = credentials.username
    return {"username": credentials.username}


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
    board = db.get_board(user_id)
    response = ai.parse(build_messages(board, request), AIResponse)
    if not response.operations:
        return ChatResponse(reply=response.reply, board=None)
    try:
        board = apply_operations(board, response.operations)
    except ValueError as error:
        logger.warning(
            "Rejected AI operations (%s): %s",
            error,
            [operation.model_dump() for operation in response.operations],
        )
        raise HTTPException(status_code=502, detail=f"The AI returned an invalid update: {error}")
    db.save_board(user_id, board)
    return ChatResponse(reply=response.reply, board=board)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
