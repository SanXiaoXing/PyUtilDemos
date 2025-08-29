import json
from typing import Dict, Any, Union

class BusDataParser:
    def __init__(self, protocol: Union[str, Dict[str, Any]]):
        """
        :param protocol: 协议文件路径 或 协议字典
        """
        if isinstance(protocol, str):
            with open(protocol, 'r', encoding='utf-8') as f:
                self.protocol = json.load(f)
        else:
            self.protocol = protocol

        if "fields" not in self.protocol:
            raise ValueError("协议格式错误：必须包含 'fields' 字段")

    @staticmethod
    def _extract_bits(data_bytes: bytes, start_bit: int, length: int) -> int:
        """
        从字节流中提取指定bit字段（高位优先）
        """
        total_bits = len(data_bytes) * 8
        if start_bit + length > total_bits:
            raise ValueError("提取的位范围超出数据长度")

        # 转为整型（大端模式）
        value = int.from_bytes(data_bytes, byteorder='big')
        # 高位在前，从总位数减去start_bit再移位
        shift = total_bits - (start_bit + length)
        mask = (1 << length) - 1
        return (value >> shift) & mask

    def parse(self, data: Union[bytes, str]) -> Dict[str, Any]:
        """
        解析一帧总线数据
        :param data: bytes 或 16进制字符串（如 '0A1B2C3D'）
        :return: dict 解析结果
        """
        if isinstance(data, str):
            data_bytes = bytes.fromhex(data)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            raise TypeError("data 必须是 bytes 或十六进制字符串")

        result = {}
        for field in self.protocol["fields"]:
            raw_value = self._extract_bits(
                data_bytes,
                field["byte_offset"],
                field["bit_length"]
            )

            ftype = field["type"]
            if ftype == "uint":
                value = raw_value
            elif ftype == "int":
                # 将值扩展为有符号数
                sign_bit = 1 << (field["length"] - 1)
                if raw_value & sign_bit:
                    # 负数补码转换
                    raw_value -= (1 << field["length"])
                scale = field.get("scale", 1)
                offset = field.get("offset", 0)
                value = raw_value * scale + offset
            elif ftype == "enum":
                value = field["values"].get(str(raw_value), f"UNKNOWN({raw_value})")
            elif ftype == "fixed":
                scale = field.get("scale", 1)
                offset = field.get("offset", 0)
                value = raw_value * scale + offset
            else:
                raise ValueError(f"未知字段类型: {ftype}")

            result[field["name"]] = value

        return result
