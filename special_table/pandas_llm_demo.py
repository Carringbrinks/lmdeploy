import os
import json
import time
import pandas as pd
from loguru import logger
from pathlib import Path
from tqdm import tqdm
from utils import openai_post, parse_output, markdown_to_csv

def main(
    excel_path: str,
    save_dir: str,
    prompts: str = "",
    max_tokens: int = 16000,
    temperture: int = 0.01,
    url="http://0.0.0.0:23333/v1",
):
    df = pd.read_excel(excel_path)
    markdown_data = df.to_markdown()

    messages=[
        {"role": "system", "content": prompts},
        {"role": "user", "content": markdown_data},
    ]
    try:
        res = openai_post(messages, max_tokens, temperture, url=url)
        res = parse_output(res)[1]
    except Exception as e:
        res = ""
        logger.error(f"{excel_path}请求报错, 报错信息为{str(e)}")

    try:
        table_info = json.loads(res)
    except Exception as e:
        logger.error(f"{excel_path}json序列化失败, 报错信息为{str(e)}")
        table_info = []

     # 假设这是你的excel路径
    excel_Path = Path(excel_path)
    file_name = excel_Path.stem

    for i, table_markdown in enumerate(table_info):
        table_name = table_markdown["table title"]
        table_data = table_markdown["table content"]
        print("=" * 100)
        print(table_name)
        print(table_data)
        table_name = table_name.replace("/", "") if table_name else str(i)
        markdown_to_csv(file_name, table_name, table_data, save_dir)

    return res


if __name__ == "__main__":

    prompt_0 = """你的任务是将markdown格式的数据转换为规范的表格数据。其中也可能包含多个表格，你需要转换为多个规范表格表格

规范表格定义：

- 每一列只能有一个明确的字段名。避免使用复合标题或多层级标题，确保每一列的数据含义清晰且唯一
- 所有数据都严格遵循列的字段名，确保了每一行的数据与对应的字段名相匹配。
- 每列的字段名都是唯一的，不能重复，且字段名可以根据markdown内容进行合并，改写
- 规范表格的行不能含有总结、汇总的行信息

数据的返回格式如下：
- 表格有标题，请提取标题；如果没有标题，请将标题设为 ""。
- 多表按照顺序依次添加到列表中
[
    {
        "table title": 返回表格标题, 字符串格式,
        "table content": 返回表格内容, markdown格式s
    }
]
"""

    
    prompt_1 = """将下面的markdown表格数据整理成规范的表格，如果含有多表，请将表格一一进行规范整理。

**注意:**
1. 整理后的表格的标题不能存在规范表中
2. 整理后的表格列标题必须是一个明确的字段名，且表格中的列标题不可以重复
3. 回复格式如下：
[
    {
        "table title": 提取表格1标题, 字符串格式,
        "table content": 提取表格1内容, markdown格式
    },
    {
        "table title": 提取表格2标题, 字符串格式,
        "table content": 提取表格2内容, markdown格式
    },
    ...

]
    """

    base_url = "http://0.0.0.0:23333/v1"
   
    save_csv_dir = "/home/scb123/PyProject/lmdeploy/special_table/pandas_llm_70_lmdeploy_1"
    excel_root = "/home/scb123/PyProject/lmdeploy/special_table/excel70"
    json_res = "res.json"
    result = []
    for excel_name in tqdm(os.listdir(excel_root)):
        excel_path = os.path.join(excel_root, excel_name)
        # print(excel_path)
        output = main(
            excel_path=excel_path, save_dir=save_csv_dir, prompts=prompt_1, url=base_url
        )
        # 假设这是你的excel路径
        excel_Path = Path(excel_path)
        file_name = excel_Path.name

        result.append({file_name: output})
    with open(os.path.join(save_csv_dir, json_res), "w") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=4))



    # df = pd.read_excel("/home/scb123/PyProject/lmdeploy/special_table/excel20/2003年中央财政预算、决算收支【山大教育】.xls")
    # markdown_data = df.to_markdown()
    # # print(markdown_data)
    # mark_down = """"""
    # messages=[
    #     {"role": "system", "content": prompt_1},
    #     {"role": "user", "content": markdown_data},
    # ]

    # res = openai_post(messages, temperture=0.01,  max_tokens=8192, url=base_url)

    # res = json.loads(res)
    # for table in res:
    #     print("="*100)
    #     print(table["table title"])
    #     print(table["table content"])

