import os
import json
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from utils import openai_post, parse_output, markdown_to_csv, encode_image


def main(
    image_path: str,
    save_dir: str,
    prompts_vlm: str = "",
    prompts_llm: str = "",
    max_tokens_vlm: int = 4096,
    max_tokens_llm: int = 4096,
    temperture_vlm: int = 0.01,
    temperture_llm: int = 0.01,
    url_vlm="http://0.0.0.0:23335/v1",
    url_llm="http://0.0.0.0:23335/v1",
):
    base64_image = encode_image(image_path)
    messages = [
        {"role": "system", "content": [{"type": "text", "text": ""}]},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompts_vlm},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        },
    ]
    try:
        mllm_res = openai_post(messages, max_tokens_vlm, temperture_vlm, url=url_vlm)
    except Exception as e:
        mllm_res = ""
        logger.error(f"{image_path}请求mllm报错, 报错信息为{str(e)}")
    print(mllm_res)

    messages=[
        {"role": "system", "content": prompts_llm},
        {"role": "user", "content": mllm_res},
    ]
    try:
        llm_res = openai_post(messages, max_tokens_llm, temperture_llm, url=url_llm)
    except Exception as e:
        llm_res = ""
        logger.error(f"{image_path}请求llm报错, 报错信息为{str(e)}")
    print(llm_res)
    res = parse_output(llm_res)[1]
    try:
        table_info = json.loads(res)
        res = table_info
    except Exception as e:
        logger.error(f"{image_path}json序列化失败, 报错信息为{str(e)}")
        table_info = []
        pass

    # 假设这是你的图片路径
    image_path = Path(image_path)
    file_name = image_path.stem

    for i, table_markdown in enumerate(table_info):
        table_name = table_markdown["table title"]
        table_data = table_markdown["table content"]
        print("=" * 100)
        print(table_name)
        print(table_data)
        table_name = table_name.replace("/", "") if table_name else str(i)
        markdown_to_csv(file_name, table_name, table_data, save_dir)

    return image_path, res


if __name__ == "__main__":

    prompt_0 = "将图片中的内容全部识别出来, 以markdown的形式输出"

    prompt_1 = """你是一个规范表格转换助手，你需要将用户给你的数据转换为规范表格。用户的数据中可能包含多个表格，你需要全部转换。
    
规范表格的定义：
- 表格中的每一行（包括标题行和数据行）都有相同数量的列。
- 表头明确且对齐，表格的内容在各列中整齐排列。
- 每列表示一个特定的字段，每行表示一条记录。
- 每个单元格只包含一个数据单元，没有跨行或跨列的合并操作。
- 表头名称应清晰、无二义性，能够准确描述对应列的数据含义。

子区域表格的判断方式：  
- 图中的内容被明确分割为多个区域，每个区域都有表格的特征（标题、表头、数据）
- 每个表格的内容有单独的标题
- 每个区域的数据互不关联，字段名称和表头也不同
- 表格的字段数量和排列方式有显著差异

返回的整体格式如下：
- 表格有标题，请提取标题；如果没有标题，请将标题设为 ""。
- 多表按照顺序依次添加到列表中
[
    {
        "table title": 返回表格标题, 字符串格式,
        "table content": 返回表格内容, markdown格式s
    }
]
"""
    
    base_url_vlm = "http://0.0.0.0:23334/v1"
    base_url_llm = "http://0.0.0.0:23336/v1"
    save_csv_dir = "/home/scb123/PyProject/lmdeploy/special_table/vlm_llm/qwen_single"
    image_root = "/home/scb123/PyProject/lmdeploy/special_table/test_table_single"
    json_res = "res.json"
    result = []
    # for image_name in tqdm(os.listdir(image_root)):
    #     img_path = os.path.join(image_root, image_name)
    #     img, output = main(
    #         image_path=img_path, save_dir=save_csv_dir, prompts_vlm=prompt_0, prompts_llm=prompt_1, url_vlm=base_url_vlm, url_llm=base_url_llm
    #     )
    #     result.append({img.name: output})
    # with open(os.path.join(save_csv_dir, json_res), "w") as f:
    #     f.write(json.dumps(result, ensure_ascii=False, indent=4))


    # base64_image = encode_image("/home/scb123/PyProject/lmdeploy/special_table/test_table_mul/1.png")
    # messages = [
    #     {"role": "system", "content": [{"type": "text", "text": ""}]},
    #     {
    #         "role": "user",
    #         "content": [
    #             {"type": "text", "text": "将图片中的内容全部识别出来, 以markdown的形式输出"},
    #             {
    #                 "type": "image_url",
    #                 "image_url": {"url": f"data:image/png;base64,{base64_image}"},
    #             },
    #         ],
    #     },
    # ]
    
    
    prompt = """"""

    mark_down = """"""

    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": mark_down},
    ]
    res = openai_post(messages, url=base_url)
    print(res)
