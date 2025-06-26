"""
根据插值表计算校准值DEMO
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import json
from pathlib import Path

CALIBCONF_PATH=str( Path(__file__).parent / 'calibconf.json')  # 插值表配置文件路径

class CalcDemo:
    def __init__(self, calibconf_path=CALIBCONF_PATH):
        self.calibconf_path = calibconf_path
        self.calibconf = self.load_calibconf()


    def load_calibconf(self):
        """加载插值表配置文件"""
        with open(self.calibconf_path, 'r') as f:
            calibconf = json.load(f)
        return calibconf
    
    
    def calc_data(self, cardname, ch, value):
        """根据插值表计算校准值"""
        calibdict = self.calibconf[cardname][str(ch)]
        
        if not calibdict:
            raise ValueError(f"未找到 {cardname} 通道 {ch} 的校准数据")

        # 确保标准值和实测值都转为 float 类型
        standvals = np.array([float(k) for k in calibdict.keys()])
        messvals = np.array([float(v) for v in calibdict.values()])

        # 排序以保证插值顺序正确
        sorted_indices = np.argsort(standvals)
        standvals = standvals[sorted_indices]
        messvals = messvals[sorted_indices]

        # 插值计算
        calib_val = np.interp(value, messvals, standvals)
        # 保留两位小数
        calib_val = round(calib_val, 2)
        return calib_val
    




calcdemo=CalcDemo()
print(calcdemo.calc_data('card_1',0,1.5))