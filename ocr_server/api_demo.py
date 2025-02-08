from openai import OpenAI
from PIL import Image
import base64
from io import BytesIO
import os
import time
import json
import re
from tqdm import tqdm

# import cv2
# import numpy as np
import fitz
import requests

prompt = """请从图片中识别并提取标题，并返回结果。请按照以下格式返回结果：

{
  "title": []
}

注意事项：
1. 标题通常位于图片的开头部分，请优先从前几行提取。
2. 如果图片中包含表格，将表格中标有“标题”或“讨论议题”的内容也视为标题并提取。
3. 正文中的小标题同样视为标题，请提取出来。
4. 如果图片中未识别到任何标题，请将列表置为空。

请确保提取的标题准确并符合上述规则。"""

# prompt = "将图片中的所有内容全部识别出来"


def pdf_to_img(pdf_path: str, save_img_path: str):
    with fitz.open(pdf_path) as pdf:
        for pg in tqdm(range(0, pdf.page_count)):
            page = pdf[pg]
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)

            # if width or height > 2000 pixels, don't enlarge the image
            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img.save(os.path.join(save_img_path + f"{pg}.png"))


def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def openai_post(image_dir: str, max_tokens: int = 512, url="http://0.0.0.0:23333/v1"):
    all_res = []
    pattern = r"\{[^{}]*\}"
    for img_file in tqdm(os.listdir(image_dir)[:10]):

        image_path = os.path.join(image_dir, img_file)
        # image_path = "./pdf_img/pdf_174.png"
        base64_image = encode_image(image_path)
        client = OpenAI(api_key="1", base_url=url)
        model_name = client.models.list().data[0].id
        start = time.time()
        res = ""
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.01,
                top_p=0.8,
                max_tokens=max_tokens,
            )
            end = time.time()
            time_cost = str(end - start) + "s"
            # print(response)
            res = response.choices[0].message.content
            matches_res = re.findall(pattern, res)[0]
            # print(matches_res)
            result = dict(
                pdf_page=img_file, vlm_res=json.loads(matches_res), time_cost=time_cost
            )
        except Exception as e:
            result = dict(pdf_page=img_file, error_vlm_res=res, time_cost="")
        all_res.append(result)

        if len(all_res) % 1 == 0 and len(all_res) > 0:
            with open("result_openai.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(all_res, indent=4, ensure_ascii=False))


def request_post(
    image_dir: str,
    model_name: str,
    max_tokens: int = 512,
    url="http://0.0.0.0:23333/v1/chat/completions",
):

    all_res = []
    pattern = r"\{[^{}]*\}"
    api_key = "1"
    headers = {"Content-Type": "application/json"}
    for img_file in tqdm(os.listdir(image_dir)):

        image_path = os.path.join(image_dir, img_file)
        base64_image = encode_image(image_path)
        start = time.time()
        res = ""
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                "temperature": 0.01,
                "top_p": 0.8,
                "max_tokens": max_tokens,
            }
            response = requests.post(
                url,
                headers=headers,
                json=payload,
            )
            end = time.time()
            time_cost = str(end - start) + "s"
            res = response.json()
            res = res["choices"][0]["message"]["content"]
            matches_res = re.findall(pattern, res)[0]
            # print(matches_res)
            result = dict(
                pdf_page=img_file, vlm_res=json.loads(matches_res), time_cost=time_cost
            )
        except Exception as e:
            result = dict(pdf_page=img_file, error_vlm_res=res, time_cost=time_cost)
        all_res.append(result)
        if len(all_res) % 1 == 0 and len(all_res) > 0:
            with open("result_intervl.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(all_res, indent=4, ensure_ascii=False))


def request_ocr_mllm(image_dir):

    for img_file in tqdm(os.listdir(image_dir)[:1]):
        print(img_file)
        image_path = os.path.join(image_dir, img_file)
        base64_image = encode_image(image_path)
        start = time.time()
        payload = {
            "ocr": {
                "app_id": "/home/qyhuang/scb/lmdeploy/ocr_server/test_json/{}.json".format(
                    img_file.split(".")[0]
                ),
                "session_id": "",
                "image": base64_image,
            },
            "model_name": "/app/weight",
            "prompt": prompt,
            "temperature": 0.01,
            # "top_p": 0.8,
            # "max_tokens": 512,
            # "rouge_1": 0.8,
            # "timeout": 100000
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url="http://127.0.0.1:23335/zjuici/ocr-mllm",
            headers=headers,
            json=payload,
        )
        end = time.time()
        time_cost = str(end - start) + "s"
        text = response.json()
        print(text)
        # json_text = text["mllm_result"]["choices"][0]["message"]["content"]
        # print(json_text)
        print("=" * 100)


# def request_ocr_mllm

if __name__ == "__main__":

    pdf_path = "/home/scb123/PyProject/lmdeploy/ocr_server/扫描全能王 2024-12-31 13.29(2).pdf"
    image_root = "./pdf_img"
    save_img_root = "/home/scb123/PyProject/lmdeploy/ocr_server/vivi"
    model_name = "mllm"
    pdf_to_img(pdf_path, save_img_root)
    # openai_post(image_root)
    # request_post(image_root, model_name)
    # request_ocr_mllm(save_img_root)
