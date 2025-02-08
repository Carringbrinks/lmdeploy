from fastapi import FastAPI
from pydantic import BaseModel
import json
from typing import Any

app = FastAPI()


class OCRRequest(BaseModel):

    app_id: str
    image: str
    session_id: str

@app.post("/get-json")
def get_json_data(pyload: OCRRequest):
    print(pyload.app_id)
    # 读取 JSON 文件
    try:
        with open(pyload.app_id, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=23334)