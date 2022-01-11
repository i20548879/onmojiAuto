import win32gui, win32ui, win32con
from ctypes import sizeof, windll
import time

class Screenshot():
    def __init__(self) -> None:
        global width,height,title,size,d
        hWnd = win32gui.FindWindow("Qt5QWindowIcon","阴阳师 - MuMu模拟器")
        left, top, right, bot = win32gui.GetWindowRect(hWnd)
        width = right - left
        height = bot - top

    def screenshot(self):
        #截图
        #返回句柄窗口的设备环境、覆盖整个窗口，包括非客户区，标题栏，菜单，边框
        hWnd = win32gui.FindWindow("Qt5QWindowIcon","阴阳师 - MuMu模拟器")
        hWndDC = win32gui.GetWindowDC(hWnd)
        #创建设备描述表
        mfcDC = win32ui.CreateDCFromHandle(hWndDC)
        #创建内存设备描述表
        saveDC = mfcDC.CreateCompatibleDC()
        #创建位图对象
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC,width,height)
        saveDC.SelectObject(saveBitMap)
        #截图至内存设备描述表
        saveDC.BitBlt((0,0), (width,height), mfcDC, (0, 0), win32con.SRCCOPY)
        result = windll.user32.PrintWindow(hWnd,saveDC.GetSafeHdc(),0)
        saveBitMap.SaveBitmapFile(saveDC,"screenshot.bmp")
        #资源释放
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hWnd, hWndDC)
        time.sleep(0.2)
        return result

if __name__ == '__main__':
    print('########## Onmoji_auto 配套截图程序 ##########\n截取图片后将保存到当前路径下，处理图片后按任意键继续截图\n注意此时新图会覆盖旧图\n按ctrl+c退出')
    s=Screenshot()
    while(True):
        input('按下任意键截图')
        s.screenshot()
        print('截图成功，保存在当前目录下')