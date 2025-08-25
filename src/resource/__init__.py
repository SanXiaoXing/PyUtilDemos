"""
资源文件
"""

from pathlib import Path


_BASE_PATH = Path(__file__).parent 
_IMG_PATH =_BASE_PATH / 'resource/image/'   
_QSS_FILE = str( _BASE_PATH / 'resource/qss/style.qss') 

AVIC_PNG=str(_IMG_PATH / 'avic.png')
BACKGROUND_1=str(_IMG_PATH/'background_1.png')
BACKGROUND_2=str(_IMG_PATH/'background_2.png')
NULL_PNG=str(_IMG_PATH/'null.png')

COM_CONNECT=str(_IMG_PATH/'com_connect.png')
COM_DISCONNECT=str(_IMG_PATH/'com_disconnect.png')

LIGHT_ERROR=str(_IMG_PATH/'light_error.png')
LIGHT_OFF=str(_IMG_PATH/'light_off.png')
LIGHT_ON=str(_IMG_PATH/'light_on.png')

LOGO_AUTOTEST=str(_IMG_PATH/'logo_AutoTest.png')  
LOGO_INTERFACETEST=str(_IMG_PATH/'logo_InterfaceTest.png')
LOGO_SIMU=str(_IMG_PATH/'logo_simu.png')
LOGO_AVIC=str(_IMG_PATH/'avic.png')

PAUSE=str(_IMG_PATH/'pause.png') 
QUIT=str(_IMG_PATH/'quit.png')
SEND=str(_IMG_PATH/'send.png')
START=str(_IMG_PATH/'start.png')

PORT=str(_IMG_PATH/'port.png')
PORT_MONITOR=str(_IMG_PATH/'port_monitor.png')
PORT_CHECK=str(_IMG_PATH/'port_check.png')


STATE_ERROR=str(_IMG_PATH/'state_error.png')
STATE_FINISHED=str(_IMG_PATH/'state_finished.png')
STATE_FREE=str(_IMG_PATH/'state_free.png')
STATE_TESTING=str(_IMG_PATH/'state_testing.png')
STATE_WARNING=str(_IMG_PATH/'state_warning.png')


def load_qss():
    """加载qss文件"""
    with open(_QSS_FILE, 'r') as f:
        return f.read()




    