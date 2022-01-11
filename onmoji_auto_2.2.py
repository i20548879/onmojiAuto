import time
import datetime,urllib.request
import win32gui, win32ui, win32con
from ctypes import sizeof, windll
import sys
import aircv as ac
import uiautomator2 as u2
import random
import subprocess
import threading

no_swipe=True #不滑动，用点击替代

class ScreenMonitor:
    def __init__(self) -> None:
        #日期检查
        intime = str(urllib.request.urlopen("http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp").read().decode())
        one = intime[:intime.rfind('"')]
        times = datetime.datetime.fromtimestamp(int(one[one.rfind('"')+1:-3]))
        year=times.year
        month=times.month
        day=times.day
        if year>2099 or month>99 or day>31:
            sys.exit("试用期已结束")
        else:
            print("日期 %i-%i-%i"%(year,month,day))
        #先设置mumu模拟器大小
        global width,height,title,size,d
        print("初始化")
        hWnd = win32gui.FindWindow("Qt5QWindowIcon","阴阳师 - MuMu模拟器")
        left, top, right, bot = win32gui.GetWindowRect(hWnd)
        width = right - left
        height = bot - top
        #雷电模拟器窗体有固定黑边标题,利用分辨率计算
        title = int(height-1080*width/2400)
        #重新调整大小
        size=0.5
        width = int(2400*size)
        height = int(1080*size + title)
        win32gui.SetWindowPos(hWnd,win32con.HWND_NOTOPMOST, 0, 0, width, height, win32con.SWP_NOZORDER)
        '''if height<570:
            sys.exit('初始化失败，请确认以下条件:\n1.调整分辨率2400×1080\n2.收起模拟器右侧\n3.调整桌面显示设置至100%后重启模拟器\n4.将模拟器置于前端')'''
        print('初始化成功')
        #连接模拟器
        d=u2.connect("127.0.0.1:7555")

    def screenshot(self):
        #截图
        '''while(trackflag):
            #防止线程冲突，如果线程里正在调用screenshot.bmp，这里就暂时休眠
            print('每隔30s状态检测')
            time.sleep(0.5)'''
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
        return result

    def clicktarget(self,imgobj,confidencevalue=0.8):
        #识别目标图片在屏幕中的坐标，并点击
        self.screenshot()
        target_img=ac.imread(imgobj)
        source_img=ac.imread(r"screenshot.bmp")
        match_result = ac.find_template(source_img,target_img,confidencevalue,rgb=True)
        if match_result:
            #获取四个点的坐标,识别的时候图内算上的标题框，所以减去
            zs,zx,ys,yx=match_result['rectangle']
            x_start=int(zs[0]/size)
            x_end=int(ys[0]/size)
            y_start=int((zs[1]-title)/size)
            y_end=int((zx[1]-title)/size)
            x=random.randint(x_start,x_end)
            y=random.randint(y_start,y_end)
            d.click(x,y)
            return 0
        else:
            return -1

    def findtarget(self,imgobj,confidencevalue=0.8):
        #在屏幕中找寻对应图片，找到返回True，找不到返回false
        self.screenshot()
        target_img=ac.imread(imgobj)
        source_img=ac.imread(r"./screenshot.bmp")
        match_result = ac.find_template(source_img,target_img,confidencevalue,rgb=True)
        if match_result:
            return True
        else:
            return False

    def wait_click(self,imgobj,confidencevalue=0.8,wait_count=-1,is_click=True):
        #持续等待某个图，直到出现,然后点击它,wait_count代表几次等待不到后就退出,-1为无限等
        while(not self.findtarget(imgobj,confidencevalue) and wait_count!=0):
            wait_count-=1
            time.sleep(2)
        if wait_count!=0:
            if is_click:
                self.clicktarget(imgobj,confidencevalue)
            return True
        else:
            return False

    def multitarget(self,imglist,isclick=[-1],confidencevalue=0.95):
        #多点匹配并点击，isclick表示要点击的img的下标，默认全点
        self.screenshot()
        source_img=ac.imread(r"./screenshot.bmp")
        Resultlist=[ac.find_template(source_img,ac.imread(imgobj),confidencevalue,rgb=True) for imgobj in imglist]
        findloc=-1
        for loc in range(len(Resultlist)):
            if Resultlist[loc]!=None:
                findloc=loc
                break
        if findloc!=-1 and (isclick==[-1] or findloc in isclick):
            zs,zx,ys,yx=Resultlist[findloc]['rectangle']
            x_start=int(zs[0]/size)
            x_end=int(ys[0]/size)
            y_start=int((zs[1]-title)/size)
            y_end=int((zx[1]-title)/size)
            x=random.randint(x_start,x_end)
            y=random.randint(y_start,y_end)
            d.click(x,y)
        return findloc

    def findsame(self,imgobj,confidencevalue=0.9):
        #在一张图中找多个适配的
        source_img=ac.imread("./screenshot.bmp")
        target_img=ac.imread(imgobj)
        match_result=ac.find_all_template(source_img,target_img,confidencevalue,rgb=True)
        return match_result

    def untrackfind(self,imgobj,confidencevalue=0.8,isclick=False):
        #用于线程中无冲突截图，方式为adb截图
        global trackflag
        trackflag=True
        target_img=ac.imread(imgobj)
        source_img=ac.imread('screenshot.bmp')
        match_result = ac.find_template(source_img,target_img,confidencevalue,rgb=True)
        trackflag=False
        if match_result:
            if isclick:
                zs,zx,ys,yx=match_result['rectangle']
                x=random.randint(zs[0],ys[0])
                y=random.randint(zs[1],zx[1])
                d.click(x,y)
            return True
        else:
            return False

    def tansuo_new(self,exe_times):
        #探索：结合新版自动换狗粮使用
        exe_count=0
        #超时没反应的计数，以便滑动
        swipe_count=0
        #一轮探索里的滑动次数
        swipe_times=0
        start_time=end_time=xiaoguai_time=shouling_time=jieshu_time=time.time()
        tansuo_start=True
        boss_flag=False
        while(exe_count<exe_times):
            findindex=-1
            while(True):
                findindex=self.multitarget(["./match/tansuo_boss.bmp","./match/tansuo_xiaoguai.bmp","./match/shengli.bmp","./match/jiesuan.bmp","./match/tansuo_rukou.bmp","./match/tansuo_k28.bmp","./match/back.bmp","./match/tansuo_denglong.bmp","./match/zhunbei.bmp","./match/xuanshang.bmp"],isclick=[0,1,4,5,7],confidencevalue=0.85)
                if findindex!=-1:
                    break
            if findindex==0:
                if time.time()-shouling_time>10:
                    shouling_time=time.time()
                    print("发现首领")
                    swipe_count=0
                    boss_flag=True
            elif findindex==1:
                if time.time()-xiaoguai_time>10:
                    xiaoguai_time=time.time()
                    print("找到小怪")
                    time.sleep(2)
                    swipe_count=0
            elif findindex==2 or findindex==3:
                if time.time()-jieshu_time>10:
                    jieshu_time=time.time()
                    print("战斗结束")
                    swipe_count=0
                x=random.randint(1700,2200)
                y=random.randint(880,1000)
                d.click(x,y)
                d.click(x,y)
            elif findindex==4:
                swipe_count=0
                if time.time()-start_time>30:
                    print("开始探索")
                    start_time=time.time()
            elif findindex==6:
                print("检测状态")
                if tansuo_start:
                    print("等待10秒检测换狗粮")
                    time.sleep(10)
                    if(self.clicktarget('./match/tansuo_lunhuan.bmp',0.95)==0):
                        print('打开自动换狗粮')
                    tansuo_start = False
                time.sleep(2)
                        
                if boss_flag and time.time()-start_time>30:
                    exe_count+=1
                    print('[%s] 探索完成%i/%i\n识别奖励，休息20s'%(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'),exe_count,exe_times))
                    find_time=time.time()
                    #30s来识别奖励
                    while(time.time()-find_time<20):
                        find2=self.multitarget(["./match/tansuo_baoxiang.bmp","./match/tansuo_dabaoxiang.bmp"])
                        if find2==0 or find2==1:
                            time.sleep(1)
                            x=random.randint(1700,2200)
                            y=random.randint(880,1000)
                            d.click(x,y)
                    boss_flag=False
                    if self.findtarget("./match/tansuo_rukou.bmp"):
                        pass
                    else:
                        self.clicktarget("./match/back.bmp")
                        time.sleep(5)
                        self.clicktarget("./match/queren.bmp")
                    end_time=time.time()
                elif time.time()-start_time>300:
                    #在探索里呆了超过5min则认为超时，退出
                    print("超时退出")
                    self.clicktarget("./match/back.bmp")
                    time.sleep(2)
                    self.clicktarget("./match/queren.bmp")
                elif time.time()-end_time>300:
                    #没有正常结算退出，重新到结束判断去
                    boss_flag=True
                    exe_count-=1
                elif swipe_count>3:
                    print('没找到怪物，滑动')
                    startx=random.randint(1600,1700)
                    starty=random.randint(375,425)
                    endx=random.randint(800,900)
                    endy=random.randint(375,425)
                    click_rx=random.randint(1800,2200)
                    click_lx=random.randint(100,1000)
                    click_y=random.randint(640,880)
                    if swipe_times%20<10:
                        if no_swipe:
                            d.click(click_rx,click_y)
                        else:
                            d.swipe(startx,starty,endx,endy)
                        swipe_times+=1
                    else:
                        #滑动了超过10次，说明有怪漏在左边，往左滑
                        if no_swipe:
                            d.click(click_lx,click_y)
                        else:
                            d.swipe(endx,starty,startx,endy)
                        swipe_times+=1
                    time.sleep(5)
                else:
                    print("等待%i/3"%swipe_count)
                    swipe_count+=1
                    time.sleep(2)
            elif findindex==8:
                #识别到准备
                self.clicktarget('./match/zhunbei.bmp')
                time.sleep(2)
            elif findindex==9:
                print('识别到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
                time.sleep(5)

    def yuhun_duiyou(self,exe_times):
            #御魂 队员模式
            exe_count=0
            #记录时间
            last_yaoqing_time=last_zhunbei_time=0
            last_jiesuan_time=time.time()
            while(exe_count<exe_times):
                findindex=-1
                while(True):
                    #持续识别
                    #findindex=self.multitarget(['./match/shengli.png','./match/jiesuan.png','./match/yaoqing_zidong.png','./match/yaoqing_jieshou.bmp','./match/zhunbei.png'])
                    findindex=self.multitarget(['./match/shengli.bmp','./match/yaoqing_zidong.bmp','./match/yaoqing_jieshou.bmp','./match/zhunbei.bmp','./match/jiesuan.bmp','./match/xuanshang.bmp'],[1,2,3])
                    if findindex!=-1:
                        break
                if findindex==0 or findindex==4:
                    #识别到胜利和结算
                    pass_jiesuan_time=time.time()-last_jiesuan_time
                    if pass_jiesuan_time>20:
                        #表示没有重复结算，更新结算时间
                        last_jiesuan_time=time.time()
                        print("结算中")
                        exe_count+=1
                        print("御魂：完成%i/%i"%(exe_count,exe_times))
                    x=random.randint(1700,2200)
                    y=random.randint(880,1000)
                    d.click(x,y)
                    d.click(x,y)
                    
                elif findindex==1 or findindex==2:
                    #识别到邀请
                    if findindex==1:
                        time.sleep(2)
                        self.clicktarget('./match/queding.bmp')
                    pass_yaoqing_time=time.time()-last_yaoqing_time
                    if pass_yaoqing_time>20:
                        last_yaoqing_time=time.time()
                        print("接受邀请")
                elif findindex==3:
                    #识别到准备
                    pass_zhunbei_time=time.time()-last_zhunbei_time
                    if pass_zhunbei_time>20:
                        last_zhunbei_time=time.time()
                        print("准备")
                elif findindex==5:
                    print('识别到封印邀请，点击叉叉')
                    x=random.randint(1390,1430)
                    y=random.randint(165,210)
                    d.click(x,y)
                    time.sleep(5)
            
    def yuhun_duizhang(self,exe_times):
        #御魂 队长模式
        exe_count=0
        #记录时间
        last_yaoqing_time=last_zhunbei_time=0
        last_jiesuan_time=last_meiren_time=time.time()
        while(exe_count<exe_times):
            findindex=-1
            while(True):
                #持续识别
                findindex=self.multitarget(['./match/shengli.bmp','./match/tiaozhan.bmp','./match/zhunbei.bmp','./match/jiesuan.bmp','./match/shibai.bmp','./match/yaoqing_jixu.bmp','./match/xuanshang.bmp'],[1,2])
                if findindex!=-1:
                    break
            if findindex==0 or findindex==3:
                #识别到胜利和结算
                pass_jiesuan_time=time.time()-last_jiesuan_time
                if pass_jiesuan_time>20:
                    #表示没有重复结算，更新结算时间
                    last_jiesuan_time=time.time()
                    print("结算中")
                    exe_count+=1
                    print("御魂：完成%i/%i"%(exe_count,exe_times))
                x=random.randint(1700,2200)
                y=random.randint(880,1000)
                d.click(x,y)
                d.click(x,y)
                #从结算后开始计算没人的时间
                last_meiren_time=time.time()
            elif findindex==1:
                #识别到挑战
                pass_yaoqing_time=time.time()-last_yaoqing_time
                if pass_yaoqing_time>20:
                    last_yaoqing_time=time.time()
                    print("点击挑战")
                    time.sleep(2)
                if time.time()-last_meiren_time>30:
                    print("超时，重新邀请队友")
                    self.clicktarget(r"./match/yaoqing_jiahao.bmp")
                    time.sleep(2)
                    self.clicktarget(r"./match/yaoqing_zuijin.bmp")
                    time.sleep(2)
                    x=random.randint(780,1150)
                    y=random.randint(270,400)
                    d.click(x,y)
                    time.sleep(2)
                    self.clicktarget(r"./match/yaoqing.bmp")
                    last_meiren_time=time.time()
            elif findindex==2:
                #识别到准备
                pass_zhunbei_time=time.time()-last_zhunbei_time
                if pass_zhunbei_time>20:
                    last_zhunbei_time=time.time()
                    print("准备")
            elif findindex==4:
                #识别到失败
                pass_jiesuan_time=time.time()-last_jiesuan_time
                if pass_jiesuan_time>20:
                    #表示没有重复结算，更新结算时间
                    last_jiesuan_time=time.time()
                    print("失败,重新邀请")
                x=random.randint(1700,2200)
                y=random.randint(880,1000)
                d.click(x,y)
                d.click(x,y)
                time.sleep(2)
                self.clicktarget("./match/queding.bmp")
                #从结算后开始计算没人的时间
                last_meiren_time=time.time()
            elif findindex==5:
                #继续邀请队友打钩
                time.sleep(2)
                self.clicktarget("./match/queding.bmp")
            elif findindex==6:
                print('识别到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
                time.sleep(5)

    def tupo_check(self):
        #用于突破检查状态，返回已击破、失败、待击破的次数，和下一个待击破的坐标
        print('检查突破状态')
        win_match=self.findsame("./match/tupo_po.bmp",confidencevalue=0.8)
        lose_match=self.findsame("./match/tupo_shibai.bmp",confidencevalue=0.9)
        meida_match=self.findsame("./match/tupo_meida.bmp",confidencevalue=0.8)
        print("当前：攻破 %i，失败 %i，待进攻 %i"%(len(win_match),len(lose_match),len(meida_match)))
        if meida_match:
            #还有没打的话就返回没打坐标
            zs,zx,ys,yx=meida_match[0]['rectangle']
            x_start=int(zs[0]/size)
            x_end=int(ys[0]/size)
            y_start=int((zs[1]-title)/size)
            y_end=int((zx[1]-title)/size)
            x=random.randint(x_start,x_end)
            y=random.randint(y_start,y_end)
        else:
            x=y=-1
        return len(win_match),len(lose_match),len(meida_match),x,y

    def tupo_new(self,exe_times,tupo_mode):
        exe_count=0
        jiesuan_time=shuaxin_time=jingong_time=0
        startflag=False
        if tupo_mode=='1':
            #全刷模式
            touxiangflag=False
            jiaotiflag=False
        elif tupo_mode=='2':
            #保级模式
            touxiangflag=False
            jiaotiflag=True
        elif tupo_mode=='3':
            #降级模式
            touxiangflag=True
            jiaotiflag=False
        while(exe_count<exe_times):
            findindex=self.multitarget(['./match/jiesuan.bmp','./match/tupo_jiemian.bmp','./match/shibai.bmp','./match/tansuo_denglong.bmp','./match/tupo_rukou.bmp','./match/tupo_queren.bmp','./match/xuanshang.bmp'],[3,4,5])
            if findindex==0:
                #识别到了结算，有可能是战斗结算，有可能是369奖励结算，通过startflag判断
                x=random.randint(2000,2400)
                y=random.randint(880,1000)
                d.click(x,y)
                d.click(x,y)
                if time.time()-jiesuan_time>15 and startflag:
                    jiesuan_time=time.time()
                    exe_count+=1
                    print('目标进攻成功')
                    print('突破执行%i/%i'%(exe_count,exe_times))
                    jiesuan_time=time.time()
                    startflag=False
                elif not startflag:
                    print('获得阶段奖励')
                time.sleep(10)
            elif findindex==1:
                #识别到了突破界面
                print('寻找目标中')
                win_times,lose_times,meida_times,x,y=self.tupo_check()
                if meida_times>0:
                    if meida_times==9 and jiaotiflag:
                        #翻转
                        print('交替')
                        touxiangflag=not touxiangflag
                    if time.time()-jingong_time>20:
                        jingong_time=time.time()
                        print('进攻')
                        d.click(x,y)
                        time.sleep(3)
                        self.clicktarget('./match/tupo_jingong.bmp')
                        time.sleep(3)
                        if self.clicktarget('./match/tupo_jingong.bmp')==0:
                            #如果点了进攻还是发现了进攻说明没挑战券了
                            time.sleep(3)
                            if self.findtarget('./match/tupo_jingong.bmp'):
                                print('没有挑战券了，结束突破')
                                x=random.randint(2000,2400)
                                y=random.randint(880,1000)
                                d.click(x,y)
                                exe_count=exe_times
                                break
                        startflag=True
                        if win_times>=3 and touxiangflag:
                            if self.wait_click('./match/tupo_touxiang.bmp',wait_count=5):
                                print('投降')
                            #防止赢的太快卡住，直接在multitarget里处理确认
                            #self.wait_click('./match/tupo_queren.bmp',wait_count=10)
                else:
                    #能打的都打完了，点刷新
                    if time.time()-shuaxin_time>30:
                        print('手动刷新')
                        isshuaxin=self.clicktarget('./match/tupo_shuaxin.bmp')
                        time.sleep(3)
                        isqueding=self.clicktarget('./match/tupo_queding.bmp')
                        time.sleep(3)
                        if isshuaxin!=0 or isqueding!=0:
                            print('刷新倒计时中，等待30s再判断')
                            time.sleep(30)
                        else:
                            shuaxin_time=time.time()
            elif findindex==2:
                x=random.randint(1700,2200)
                y=random.randint(880,1000)
                d.click(x,y)
                d.click(x,y)
                if time.time()-jiesuan_time>15:
                    jiesuan_time=time.time()
                    print('目标进攻失败')
                    jiesuan_time=time.time()
                    startflag=False
                    time.sleep(5)
            elif findindex==6:
                print('识别到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
                time.sleep(5)

    def danshua(self,exe_times):
        #单刷副本，目前支持御魂、觉醒、业原火、御灵
        exe_count=0
        tiaozhan_time=0
        while(exe_count<exe_times):
            findloc=self.multitarget(['./match/tiaozhan_danshua.bmp','./match/shengli.bmp','./match/jiesuan.bmp','./match/shibai.bmp','./match/tiaozhan_juexing.bmp','./match/xuanshang.bmp'],isclick=[0,4])
            #没有加失败的处理是因为失败也会有统计条，可以一并处理
            if findloc==0 or findloc==4:
                if time.time()-tiaozhan_time>15:
                    #挑战时间从上一次点挑战开始计时
                    print('点击挑战')
                    tiaozhan_time=last_time=time.time()
            elif findloc==1 or findloc==2:
                x=random.randint(1700,2200)
                y=random.randint(800,1000)
                d.click(x,y)
                d.click(x,y)
                if time.time()-last_time>15:
                    #last_time从开始挑战计时，防止重复结算
                    last_time=time.time()
                    exe_count+=1
                    print('副本完成%i/%i'%(exe_count,exe_times))
            elif findloc==3:
                x=random.randint(1700,2200)
                y=random.randint(800,1000)
                d.click(x,y)
                d.click(x,y)
                if time.time()-last_time>15:
                    #last_time从开始挑战计时，防止重复结算
                    last_time=time.time()
                    print('失败')
            elif findloc==5:
                print('识别到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
                time.sleep(5)

    def huanzhenrong(self,groupnum):
        #更换队伍（御魂），groupnum为1-4
        #更换队伍预设的坐标，x相同
        x_left=1710
        x_right=1750
        #四个队伍预设窗口的y坐标
        y_top=[230,450,675,900]
        y_bottom=[260,485,710,935]
        x=random.randint(x_left,x_right)
        y=random.randint(y_top[groupnum-1],y_bottom[groupnum-1])
        while(True):
            findloc=self.multitarget(['./match/shishenlu.bmp','./match/yushe.bmp','./match/juanzhou_weikai.bmp','./match/chacha.bmp','./match/back.bmp','./match/xuanshang.bmp','./match/queren.bmp'])
            if findloc==0:
                print('进入式神录，准备更换队伍')
                #睡五秒防止获取到运动着的预设
                time.sleep(5)
            elif findloc==1:
                print('点击预设')
                time.sleep(5)
                print('更换队伍%i'%groupnum)
                d.double_click(x,y)
                time.sleep(2)
                if self.clicktarget('./match/queding.bmp')==0:
                    print('确定')
                else:
                    print('更换失败，可能为正在使用的队伍')
                time.sleep(5)
                self.clicktarget('./match/shishenlu_fanhui.bmp')
                print('更换完毕，回到庭院')
                time.sleep(3)
                return
            elif findloc==5:
                print('识别到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
                time.sleep(5)
            else:
                #其他操作点击后
                time.sleep(2)
    
    def tansuo_and_tupo(self,tansuo_times,tupo_times,tupo_mode,sleep_time,loop_times):
        loop_count=0
        while(loop_count<loop_times):
            print("——————任务组循环%i/%i——————"%(loop_count,loop_times))
            self.huanzhenrong(1)
            self.tansuo_new(tansuo_times)
            self.huanzhenrong(2)
            self.tupo_new(tupo_times,tupo_mode)
            print('当前时间 %s'%datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
            print('休息%is'%sleep_time)
            time.sleep(sleep_time)
            loop_count+=1



    '''
    def thread_task(self,isjiyang=False):
        #开出的线程分支，只要用来执行检测突发事件或定时功能,暂时停用
        while(not stop_thread):
            #如果stop_thread为false则一直执行
            if self.untrackfind('./match/xuanshang.bmp'):
                print('检测到封印邀请，点击叉叉')
                x=random.randint(1390,1430)
                y=random.randint(165,210)
                d.click(x,y)
            time.sleep(30)
    '''
        

if __name__ == '__main__':
    
    print('########## Onmoji_auto v2.2 ##########')
    print('1.请让模拟器在前台运行并设置分辨率为2400×1080\n2.收起模拟器右边界')
    print('3.在桌面右键-显示设置-缩放与布局改为100%\n')

    bot=ScreenMonitor()


    #引导并执行功能
    auto_start_time=time.time()
    print('————————————————————')
    mode=input("[执行功能]：\n1.探索\n2.队长模式\n3.队员模式\n4.结界突破\n5.单刷模式:支持御魂(大蛇、业原火、日轮、永生)、觉醒、御灵\n6.探索突破穿插\n7.活动：长草期\n[功能选择]: ")
    exe_count=input("[执行/任务组次数]: ")
    print("若脚本长时间无响应，请自行截图并替换match文件夹下的图片")
    try:
        if mode=='1':
            input("开始探索，请设置完狗粮后庭院或探索界面启动。")
            bot.tansuo_new(int(exe_count))
        elif mode=='2':
            input("队长模式，支持超时重新邀请队友，需确保需要邀请的队友在最近的第一个位置。支持：觉醒、御魂\n请手动开一把后自动邀请队友，在房间按回车开启脚本")
            bot.yuhun_duizhang(int(exe_count))
        elif mode=='3':
            input("队员模式，可自动接受邀请，建议房间启动防止计时异常。支持：觉醒、御魂\n按回车开启\n————————————————————")
            bot.yuhun_duiyou(int(exe_count))
        elif mode=='4':
            tupo_mode=input("结界突破，需锁定阵容\n1.全刷模式:正常全打 2.保级模式：打3投6与全打交替 3.降级模式：每轮都打3投6\n[模式选择]: ")
            input("在突破界面按回车开启\n——————————————————————————")
            bot.tupo_new(int(exe_count),tupo_mode)
        elif mode=='5':
            input("单刷模式：请在对应界面锁定阵容\n按回车开启\n————————————————————————")
            bot.danshua(int(exe_count))
        elif mode=='6':
            tansuo_times=input("探索突破穿插模式：\n输入单次循环任务组内[探索次数]: ")
            tupo_times=input("输入单次循环任务组内[突破次数]: ")
            tupo_mode=input("1.全刷模式:正常全打 2.保级模式：打3投6与全打交替 3.降级模式：每轮都打3投6\n[突破模式设定]: ")
            sleep_time=input("每执行完一次任务组，[休息时间]: ")
            input("设定完毕，请将预设队伍1设置为探索阵容，预设队伍2设置为突破阵容\n请先设置好自动轮换的狗粮，脚本将自动打开轮换开关\n庭院中按回车启动，庭院设置初始皮肤\n————————————————————")
            bot.tansuo_and_tupo(int(tansuo_times),int(tupo_times),tupo_mode,int(sleep_time),int(exe_count))
        else:
            print("请输入正确的数字编号")
    except KeyboardInterrupt:
        print('————————————\n手动停止')
    stop_thread=True
    runtime=time.time()-auto_start_time
    h=int(runtime/3600)
    m=int((runtime-3600*h)/60)
    s=int(runtime-3600*h-60*m)
    print('结束运行，本次耗时:%i小时%i分钟%i秒'%(h,m,s))
    input('按回车键退出')
        
    
