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
        :param data_bytes: 原始字节流
        :param start_bit: 起始bit位置（0表示第1位，按bit顺序递增）
        :param length: 提取的bit长度
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
            # 计算字段起始 bit
            start_bit = field["byte_offset"] * 8 + field.get("bit_offset", 0)
            bit_length = field["bit_length"]

            # 提取原始值
            raw_value = self._extract_bits(data_bytes, start_bit, bit_length)

            ftype = field["type"]
            if ftype == "uint":
                value = raw_value
            elif ftype == "int":
                # 有符号数补码转换
                sign_bit = 1 << (bit_length - 1)
                if raw_value & sign_bit:
                    raw_value -= (1 << bit_length)
                scale = float(field.get("scale", 1.0))
                offset = float(field.get("offset", 0.0))
                value = raw_value * scale + offset
            elif ftype == "enum":
                enum_map = field.get("map", {})
                value = enum_map.get(str(raw_value), f"UNKNOWN({raw_value})")
            elif ftype == "fixed":
                scale = float(field.get("scale", 1.0))
                offset = float(field.get("offset", 0.0))
                value = raw_value * scale + offset
            else:
                raise ValueError(f"未知字段类型: {ftype}")

            result[field["name"]] = value

        return result
