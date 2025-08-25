# -*- coding: utf-8 -*-
import logging
import os
import datetime
from common.Comm_Function import CommFunciton as comm



log_filename = f"log_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
log_filepath = os.path.join(comm.get_path('logs'), log_filename)

"""格式器"""
simple = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)-9s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S")


"""处理器"""
#终端显示
console=logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(simple)
#日志文件
filehandler=logging.FileHandler(filename=log_filepath,mode='a',encoding='utf-8')
filehandler.setLevel(logging.INFO)
filehandler.setFormatter(simple)



"""记录器"""
log_AutoTest = logging.getLogger("自动测试软件")
log_AutoTest.setLevel(logging.DEBUG)
log_AutoTest.addHandler(console)
log_AutoTest.addHandler(filehandler)


log_Interface_Test = logging.getLogger("接口测试软件")
log_Interface_Test.setLevel(logging.DEBUG)
log_Interface_Test.addHandler(console)
log_Interface_Test.addHandler(filehandler)


log_HM_Test = logging.getLogger("健康管理软件")
log_HM_Test.setLevel(logging.DEBUG)
log_HM_Test.addHandler(console)
log_HM_Test.addHandler(filehandler)


log_Simu_Test = logging.getLogger("仿真测试软件")
log_Simu_Test.setLevel(logging.DEBUG)
log_Simu_Test.addHandler(console)
log_Simu_Test.addHandler(filehandler)

log_Card_Test = logging.getLogger("板卡消息")
log_Card_Test.setLevel(logging.DEBUG)
log_Card_Test.addHandler(console)
log_Card_Test.addHandler(filehandler)






       
        
        


        
