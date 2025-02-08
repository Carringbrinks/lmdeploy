import re
import json
import httpx
import traceback
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from util import process_ocr_result

app = FastAPI()

# OCR URL
SERVICE_YOUTU_URL = "http://0.0.0.0:23334/get-json"

# MLLM URL
SERVICE_MLLM_URL = "http://127.0.0.1:23333/v1/chat/completions"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer 1"}


class OCRMLLMRequest(BaseModel):

    model_name: str
    prompt: str
    ocr: dict = {}
    prompt:  Optional[str] = ""
    temperature: Optional[float] = 0.01
    top_p: Optional[float] = 0.8
    max_tokens: Optional[int] = 512
    rouge_1: Optional[float] = 0.8
    timeout: Optional[int] = 100000


@app.post("/zjuici/ocr-mllm")
async def combine_data(payload: OCRMLLMRequest):
    # 定义大模型结果匹配规则
    pattern = r"\{[^{}]*\}"
    # ocr和mllm服务请求状态码初始化
    ocr_status = -1
    mllm_status = -1
    try:
        # 请求第一个服务：OCR
        async with httpx.AsyncClient(timeout=payload.timeout) as client:
            ocr_payload = payload.ocr
            response_ocr = await client.post(SERVICE_YOUTU_URL, json=ocr_payload)
            response_ocr.raise_for_status()
            ocr_status = response_ocr.status_code

            try:
                data_ocr = response_ocr.json()
                # print(data_ocr)
                # print("-" * 100)
            except json.JSONDecodeError as e:
                error_details = traceback.format_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR服务响应无法解析为JSON，状态码: {ocr_status}, 错误信息: {error_details}",
                )

        # 如果MLLM接口出现任何报错，返回腾讯结果，和接口报错信息，不影响服务功能
        try:

            payload_mllm = {
                "model": payload.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": payload.prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{payload.ocr.get('image', '')}"
                                },
                            },
                        ],
                    }
                ],
                "temperature": payload.temperature,
                "top_p": payload.top_p,
                "max_tokens": payload.max_tokens,
            }
            # 请求第二个服务：MLLM
            async with httpx.AsyncClient(timeout=payload.timeout) as client:
                response_mllm = await client.post(
                    SERVICE_MLLM_URL, headers=HEADERS, json=payload_mllm
                )
                mllm_status = response_mllm.status_code
                response_mllm.raise_for_status()  # 检查HTTP状态码是否为错误

                try:
                    data_mllm = response_mllm.json()
                    data_mllm_content = data_mllm["choices"][0]["message"]["content"]
                    mmllm_res = re.findall(pattern, data_mllm_content)
                    # print(mmllm_res)
                    if mmllm_res:
                        mmllm_res = mmllm_res[0]
                        mmllm_res = json.loads(mmllm_res)
                    else:
                        mmllm_res = {"title":[]} 
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    error_info = traceback.format_exc()
                    raise HTTPException(
                        status_code=500,
                        detail=f"解析MLLM响应数据时出错，状态码: {mllm_status}, 错误信息: {error_info}",
                    )

            # 根据mllm的结果修正ocr的结果
            try:
                new_ocr = process_ocr_result(data_ocr, mmllm_res.get("title", ""))
                new_ocr.update({"mllm_res": mmllm_res})
                return new_ocr
            except Exception as e:
                error_info = traceback.format_exc()
                raise HTTPException(
                    status_code=500, detail=f"处理OCR和MLLM数据时发生错误: {error_info}"
                )

        except Exception as e:
            error_details = {
                "type": type(e).__name__,
                "message": str(e) + " mllm接口报错",
            }
            data_ocr.update({"mllm_res": error_details})
            return data_ocr

    except httpx.HTTPStatusError as e:
        error_info = traceback.format_exc()
        error_details = {
            "type": type(e).__name__,
            "message": str(error_info) or "无详细错误信息",
        }
        raise HTTPException(
            status_code=500,
            detail=f"HTTP请求错误，错误类型: {error_details['type']}, 错误信息: {error_details['message']}, OCR请求状态码: {ocr_status}, MLLM请求状态码: {mllm_status}",
        )
    except httpx.RequestError as e:
        error_info = traceback.format_exc()
        error_details = {
            "type": type(e).__name__,
            "message": str(error_info) or "无详细错误信息",
        }
        raise HTTPException(
            status_code=500,
            detail=f"MLLM服务网络错误，错误类型: {error_details['type']}, 错误信息: {error_details['message']}",
        )
    except Exception as e:
        error_info = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"错误信息: {error_info}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=23335)
