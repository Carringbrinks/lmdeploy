import base64
import os
import time
import csv
import re
from loguru import logger
from openai import OpenAI
from functools import wraps

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function '{func.__name__}' took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

@timeit
def openai_post(
   message: list[dict], max_tokens: int = 4096, temperture=0.01, url="http://0.0.0.0:23333/v1"
):

    client = OpenAI(api_key="1", base_url=url)
    model_name = client.models.list().data[0].id
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=message,
            temperature=temperture,
            max_tokens=max_tokens,
        )
        res = response.choices[0].message.content
        logger.info(response.usage)
        logger.info(res)
    except Exception as e:
        error_message = f"接口请求失败,错误信息{str(e)}"
        res = error_message
        logger.error(error_message)
    return res

  
def parse_output(code_block):

    code_block = code_block.strip()
    # 定义正则表达式模式，考虑了起始标记、可选的语言标识符以及内容。
    pattern = re.compile(r"^```\s*(\w*)\s*([\s\S]*?)\s*```$", re.DOTALL)
    match = pattern.match(code_block)

    if match:
        lang_identifier, content = match.groups()
        lang_identifier = lang_identifier.strip() if lang_identifier else ""
        content = content.strip() if content else ""
        return ["```", content, "```"]

    else:
        return ["```", code_block.strip(), "```"]


def markdown_to_csv(
    file_name,
    table_name,
    table_content,
    save_dir,
):

    lines = table_content.replace("```", "").replace("markdown", "").strip().split("\n")
    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    data = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines[2:]]

    # 保存为 CSV 文件
    os.makedirs(os.path.join(save_dir, file_name), exist_ok=True)
    output_file = os.path.join(save_dir, file_name, f"{table_name}.csv")
    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # 写入表头
        writer.writerows(data)  # 写入数据

    logger.info(f"表格已保存为 {output_file}")
