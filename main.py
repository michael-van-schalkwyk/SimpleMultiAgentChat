# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json
import httpx
from typing import List

app = FastAPI()

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory chat history
chat_history = []

# Connected WebSocket clients
clients: List[WebSocket] = []

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

# Correct model name
MODEL_NAME = "llama3.2:3b-instruct-q4_K_M"

async def generate_response(prompt: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OLLAMA_API,
                json={"model": MODEL_NAME, "prompt": prompt},
                timeout=30.0  # Add a timeout
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the response line by line
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            full_response += data["response"]
                    except json.JSONDecodeError:
                        print(f"Failed to parse line: {line}")
            
            return full_response.strip()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error: Unable to generate response. Status code: {e.response.status_code}"
        except httpx.RequestError as e:
            print(f"An error occurred while requesting: {e}")
            return "Error: Unable to connect to the language model service."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Error: An unexpected error occurred while generating the response."

@app.get("/")
async def get():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            chat_history.append(message)

            if message["content"].startswith("@agent1"):
                prompt = message["content"].replace("@agent1", "", 1).strip()
                response = await generate_response(f"You are Agent 1. Please respond to the following: {prompt}")
                response_message = {"role": "agent1", "content": response}
            elif message["content"].startswith("@agent2"):
                prompt = message["content"].replace("@agent2", "", 1).strip()
                response = await generate_response(f"You are Agent 2. Please respond to the following: {prompt}")
                response_message = {"role": "agent2", "content": response}
            else:
                response_message = None

            if response_message:
                chat_history.append(response_message)
                for client in clients:
                    await client.send_json(response_message)

    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception as e:
        print(f"An error occurred in the WebSocket connection: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)