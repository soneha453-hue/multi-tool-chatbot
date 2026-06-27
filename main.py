from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph_bot import chatbot, retriev_thread, delete_thread

app = FastAPI(title="Multi-Tool Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return JSONResponse({"status": "Multi-Tool Chatbot API is running! "})


class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ThreadRequest(BaseModel):
    thread_id: str

@app.post("/chat")
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = chatbot.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config
    )
    reply = result["messages"][-1].content
    return {"reply": reply}


@app.get("/threads")
def get_threads():
    threads = retriev_thread()
    result = []
    for tid in threads:
        config = {"configurable": {"thread_id": tid}}
        state = chatbot.get_state(config)
        preview = tid  # fallback
        if state and state.values.get("messages"):
            for msg in state.values["messages"]:
                if msg.__class__.__name__ == "HumanMessage":
                    text = msg.content.strip()
                    preview = text[:40] + ("..." if len(text) > 40 else "")
                    break
        result.append({"thread_id": tid, "preview": preview})
    return {"threads": result}


@app.delete("/thread")
def remove_thread(req: ThreadRequest):
    delete_thread(req.thread_id)
    return {"status": "deleted", "thread_id": req.thread_id}


@app.get("/history/{thread_id}")
def get_history(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = chatbot.get_state(config)
    messages = []
    if state and state.values.get("messages"):
        for msg in state.values["messages"]:
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            messages.append({"role": role, "content": msg.content})
    return {"messages": messages}