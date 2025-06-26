import os 
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import glob
from datetime import datetime

from reuse_page.Ui_LogCheckForm import *





class LogCheckForm(QWidget,Ui_LogCheckForm):
    def __init__(self):
        super(LogCheckForm,self).__init__()
        self.setupUi(self)
        self.Load_qss()
        self.InitUI()



    def InitUI(self):
        self.setWindowTitle('历史日志')
        strdate=datetime.now().strftime('%Y-%m-%d')
        self.Get_Log_File_By_Date(strdate)
        self.Set_Log_Date()
        self.calendarWidget.selectionChanged.connect(lambda:self.Get_Log_File_By_Date(self.calendarWidget.selectedDate().toString("yyyy-MM-dd")))

    def Set_Log_Date(self):
        logs_folder=comm.get_path('logs')
        log_files=glob.glob(os.path.join(logs_folder,"*.log"))
        for logfile in log_files: 
            date = os.path.basename(logfile)
            date = date.split('_')[1].split('.')[0]
            date = datetime.strptime(date, '%Y-%m-%d').date()
            format = QTextCharFormat()
            format.setBackground(QColor(180,238,180))
            self.calendarWidget.setDateTextFormat(date, format)
            
        

    def Get_Log_File_By_Date(self,date):
        logs_folder=comm.get_path('logs')
        log_files=glob.glob(os.path.join(logs_folder,"*.log"))
        for logfile in log_files:
            if date in logfile:
                with open(logfile,'r',encoding='utf-8') as file:
                    log_content=file.read()
                    self.plainTextEdit_log.clear()
                    self.plainTextEdit_log.appendPlainText(log_content)

            

    def Load_qss(self):
        qssfile=comm.get_path('resources\qss\style.qss')
        with open(qssfile, 'r') as f:
            self.setStyleSheet(f.read())



if __name__ == "__main__":
    app =QtWidgets.QApplication(sys.argv)
    Tool = LogCheckForm()
    Tool.show()
    sys.exit(app.exec())