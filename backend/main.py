"""
FastAPI 主应用
提供：
- POST /api/run  - 同步执行任务（等待完整结果）
- WS  /ws/run   - WebSocket 实时流式执行（推荐）
- GET /api/health - 健康检查
- GET /         - 前端页面
"""
import asyncio
import json
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from backend.graph.build_graph import build_graph
from langchain_core.messages import HumanMessage


# ── 应用生命周期：预编译图（避免首次请求延迟）─────────────────
_compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _compiled_graph
    print("正在编译 Agent 图...")
    _compiled_graph = build_graph()
    print("Agent 图编译完成，服务就绪。")
    yield
    print("服务关闭。")


app = FastAPI(
    title="企业级多Agent任务执行平台",
    description="基于 DeepSeek + LangGraph 的智能任务协作系统",
    version="2.0.0",
    lifespan=lifespan,
)

# 挂载前端静态文件
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# ── 请求/响应模型 ────────────────────────────────────────────
class TaskRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class TaskResponse(BaseModel):
    status: str
    final_report: Optional[str]
    execution_log: list[str]
    plan: list[dict]


# ── REST API ─────────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    """返回前端页面"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "前端文件未找到，请访问 /docs 使用 API"}


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "model": "deepseek-chat",
        "graph_ready": _compiled_graph is not None,
    }


@app.post("/api/run", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """
    同步执行任务，等待完整结果。
    适合简单集成，不支持实时进度查看。
    """
    if not _compiled_graph:
        raise HTTPException(status_code=503, detail="Agent 图尚未就绪")

    try:
        initial_state = {
            "messages": [HumanMessage(content=request.query)],
            "user_input": request.query,
            "next": "",
            "plan": [],
            "current_task_index": 0,
            "tool_results": {},
            "execution_log": [],
            "final_report": None,
            "error": None,
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, _compiled_graph.invoke, initial_state
        )

        return TaskResponse(
            status="completed",
            final_report=result.get("final_report"),
            execution_log=result.get("execution_log", []),
            plan=[
                {"id": t["id"], "description": t["description"],
                 "agent": t["agent"], "status": t["status"]}
                for t in result.get("plan", [])
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── WebSocket 实时流式执行 ────────────────────────────────────
@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    """
    WebSocket 实时执行端点。
    客户端发送 JSON: {"query": "..."}
    服务端推送各阶段状态：
      {"type": "log",    "data": "..."}        执行日志
      {"type": "plan",   "data": [...]}        任务计划
      {"type": "report", "data": "..."}        最终报告
      {"type": "done",   "data": "completed"}  完成信号
      {"type": "error",  "data": "..."}        错误信息
    """
    await websocket.accept()

    try:
        # 接收查询
        raw = await websocket.receive_text()
        payload = json.loads(raw)
        query = payload.get("query", "").strip()

        if not query:
            await websocket.send_json({"type": "error", "data": "请求内容不能为空"})
            return

        await websocket.send_json({"type": "log", "data": f"收到任务: {query}"})
        await websocket.send_json({"type": "log", "data": "正在初始化 Agent 图..."})

        if not _compiled_graph:
            await websocket.send_json({"type": "error", "data": "Agent 图尚未就绪"})
            return

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "user_input": query,
            "next": "",
            "plan": [],
            "current_task_index": 0,
            "tool_results": {},
            "execution_log": [],
            "final_report": None,
            "error": None,
        }

        # 使用 LangGraph stream 模式，逐步推送每个节点的输出
        loop = asyncio.get_event_loop()

        def run_graph_streaming():
            """在线程池中运行图，收集所有流式事件"""
            events = []
            for event in _compiled_graph.stream(initial_state, stream_mode="updates"):
                events.append(event)
            return events

        events = await loop.run_in_executor(None, run_graph_streaming)

        final_state = {}
        for event in events:
            for node_name, node_output in event.items():
                # 推送执行日志
                for log in node_output.get("execution_log", []):
                    await websocket.send_json({"type": "log", "data": log})
                    await asyncio.sleep(0.05)  # 轻微延迟，让前端感受到逐步更新

                # 推送任务计划（Planner 节点）
                if "plan" in node_output:
                    plan_data = [
                        {"id": t["id"], "description": t["description"],
                         "agent": t["agent"], "status": t["status"]}
                        for t in node_output["plan"]
                    ]
                    await websocket.send_json({"type": "plan", "data": plan_data})

                # 推送最终报告（Report 节点）
                if node_output.get("final_report"):
                    await websocket.send_json({
                        "type": "report",
                        "data": node_output["final_report"]
                    })

                final_state.update(node_output)

        await websocket.send_json({"type": "done", "data": "completed"})

    except WebSocketDisconnect:
        print("WebSocket 客户端断开连接")
    except json.JSONDecodeError:
        await websocket.send_json({"type": "error", "data": "无效的 JSON 格式"})
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
