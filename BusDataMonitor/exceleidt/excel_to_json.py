import json
import pandas as pd
from pathlib import Path


EXCEL_FILE = str(Path(__file__).parent / 'protocol/protocol_template.xlsx')
JSON_PATH= str(Path(__file__).parent / 'protocol')


def parse_enum_map(enum_str):
    """解析枚举映射字符串 '0:Idle,1:Active' → {'0':'Idle','1':'Active'}"""
    if pd.isna(enum_str):
        return {}
    mapping = {}
    for item in str(enum_str).split(","):
        kv = item.split(":")
        if len(kv) == 2:
            key, val = kv
            mapping[key.strip()] = val.strip()
    return mapping



def excel_to_json(excel_path: str, json_path: str):
    # 读取 Excel 文件
    df = pd.read_excel(excel_path)

    # 必须包含以下列
    required_cols = ["Name", "ByteOffset", "BitOffset","BitLength", "Type"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Excel 缺少必须的列: {col}")

    fields = []
    for _, row in df.iterrows():
        field = {
            "name": row["Name"],
            "byte_offset": int(row["ByteOffset"]),
            "bit_offset": int(row["BitOffset"]),
            "bit_length": int(row["BitLength"]),
            "type": str(row["Type"]).lower(),
            "description": str(row.get("Description", "")),
        }

        # 如果是 enum 类型，解析成 dict
        if field["type"] == "enum":
            enum_str = row.get("EnumMap/Value", "")
            if isinstance(enum_str, str) and enum_str.strip():
                try:
                    field["map"] = parse_enum_map(row.get("EnumMap/Value", ""))
                except json.JSONDecodeError:
                    raise ValueError(f"枚举定义格式错误: {enum_str}")
            else:
                field["map"] = {}

        # 如果是 fixed 类型，解析缩放比例
        elif field["type"] == "fixed":
            scale_val = row.get("Scale", 1.0)
            offset_val = row.get("Offset", 0.0)
            field["scale"] = float(scale_val) if pd.notna(scale_val) else 1.0
            field["offset"] = float(offset_val) if pd.notna(offset_val) else 0.0
 
        fields.append(field)

    # 输出 JSON
    protocol_json = {
        "protocol_name":"name",  
        "protocol_length":64,
        "fields": fields
    }
    json_path = Path(json_path)
    json_path.write_text(json.dumps(protocol_json, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"协议 JSON 已生成：{json_path}")

# 使用示例
# excel_to_json("协议定义.xlsx", "protocol.json")
