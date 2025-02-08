import copy
import jieba
from rouge_chinese import Rouge

# 创建ROUGE评估器
rouge = Rouge()


def compute_rouge(reference, hypothesis):
    # 分词处理
    reference_tokens = " ".join(jieba.lcut(reference))
    hypothesis_tokens = " ".join(jieba.lcut(hypothesis))
    print(reference_tokens)
    print(hypothesis_tokens)
    # 比对的字符串一个不能为空
    if reference_tokens and hypothesis_tokens:
        scores = rouge.get_scores(reference_tokens, hypothesis_tokens)
        result = scores[0]["rouge-1"]["r"]
    else:
        result=0.0
    return result


def process_element(element: dict, title_text: list, similarity_threshold: float = 0.8):
    def is_title(text):
        return any(
            compute_rouge(text, title) > similarity_threshold for title in title_text
        )

    if not element.get("elements"):
        if is_title(element["text"]):
            element["type"] = "test_title"
        return element
    else:
        new_element = []
        for elem in element["elements"]:
            text = elem["text"]
            if is_title(text):
                elem["type"] = "test_title"
            elem = process_element(elem, title_text)
            new_element.append(elem)
        element["elements"] = new_element
        return element


def process_ocr_result(ocr_res: dict, title_text: list):
    recognize_list = ocr_res["recognize_list"]
    for i, rec in enumerate(recognize_list):
        new_elements = []
        if rec["element_content"]:
            for element in rec["element_content"]["elements"]:
                new_element = process_element(element, title_text)
                new_elements.append(new_element)
            ocr_res["recognize_list"][i]["element_content"]["elements"] = new_elements

    return ocr_res


if __name__ == "__main__":
    pass

    # 测试数据解析函数process_ocr_result
    # import json

    # with open(
    #     "/home/qyhuang/scb/lmdeploy/ocr_server/test.json", "r", encoding="utf-8"
    # ) as f, open(
    #     "/home/qyhuang/scb/lmdeploy/ocr_server/test_res.json", "w", encoding="utf-8"
    # ) as f1:
    #     data = json.load(f)
    #     new_data = process_ocr_result(data, ["中国共产党", "入党志愿书"])

    #     f1.write(json.dumps(new_data, indent=4, ensure_ascii=False))

    # 测试rouge函数
    reference_text = "人党申请书"
    hypothesis_text = "入党申请书"
    rouge_scores = compute_rouge(reference_text, hypothesis_text)
    print(rouge_scores)
