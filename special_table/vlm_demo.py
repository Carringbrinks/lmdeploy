import os
import json
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from utils import openai_post, parse_output, markdown_to_csv, encode_image


def main(
    image_path: str,
    save_dir: str,
    prompts: str = "",
    max_tokens: int = 4096,
    temperture: int = 0.01,
    url="http://0.0.0.0:23333/v1",
):
    base64_image = encode_image(image_path)
    messages = [
        {"role": "system", "content": [{"type": "text", "text": ""}]},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompts},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        },
    ]
    try:
        mllm_res = openai_post(messages, max_tokens, temperture, url=url)
    except Exception as e:
        mllm_res = ""
        logger.error(f"{image_path}请求报错, 报错信息为{str(e)}")
    print(mllm_res)

    res = parse_output(mllm_res)[1]
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

    prompt = """你是一个表格识别提取助手，你需要将你识别到的表格内容整理成规范的表格。图片中可能包含多个子区域表格，你也需要将其识别并规范。

规范表格的定义：
- 表格中的每一行都有相同数量的列。
- 表头明确且对齐，表格的内容在各列中整齐排列。
- 每列表示一个特定的字段，每行表示一条记录。
- 每个单元格只包含一个数据单元，没有跨行或跨列的合并操作。
- 列名称应清晰、无二义性且不能重复，能够准确描述对应列的数据含义。

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
        "table content": 返回表格内容, markdown格式
    }
]

"""
    # prompt = "识别出图片中的全部内容"
    base_url = "http://0.0.0.0:23333/v1"
    # img_path = (
    #     "/home/scb123/PyProject/lmdeploy/special_table/vlm_test_table_single/0.png"
    # )
    save_csv_dir = "/home/scb123/PyProject/lmdeploy/special_table/vlm/internvl_single"
    image_root = "/home/scb123/PyProject/lmdeploy/special_table/test_table_single"
    json_res = "res.json"
    result = []
    for image_name in tqdm(os.listdir(image_root)):
        img_path = os.path.join(image_root, image_name)
        img, output = main(
            image_path=img_path, save_dir=save_csv_dir, prompts=prompt, url=base_url
        )
        result.append({img.name: output})
    with open(os.path.join(save_csv_dir, json_res), "w") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=4))
