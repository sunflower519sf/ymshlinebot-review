from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi

from re import compile
import os

import time
from datetime import datetime,timedelta



# user id 轉名稱
from linebot.exceptions import LineBotApiError

# 寫入google 試算表
import pygsheets

# 導入紀錄
from googledrive import fileupdata



import json

with open('setting.json', 'r', encoding='utf8') as jfile:
    jdata = json.load(jfile)
with open('userid.json', 'r', encoding='utf8') as juserfile:
    juser = json.load(juserfile)
with open('textreply.json', 'r', encoding='utf8') as jspefile:
    jspe = json.load(jspefile)
with open('banid.json', 'r', encoding='utf8') as jspefile:
    jban = json.load(jspefile)

sched = BackgroundScheduler()

app = Flask(__name__)

password = None
# userids = []

sayallrecord = []
usernewsay = None




textmessages = "所有對話紀錄：\n"
bancheck = True

# 臨時權限密碼設定
temppass = ""
temppass_admin = ""

# class MyEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, bytes):
#             return str(obj, encoding='utf-8')
#         return json.JSONEncoder.default(self, obj)


def hello_msg_check():
    gc = pygsheets.authorize(service_file='./goldkey.json')
    sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1TjbpD1ba9n7n7MnZTNE_siGwqswYH7PgCNscEVvbeWw/')
    wks_list = sht.worksheets()
    print(wks_list)
    wks = sht[0]
    bkcoun = "H1"
    getcf = str(wks.cell(bkcoun))
    getcf = getcf.replace(f"<Cell {bkcoun} '", "").replace("'>", "")
    try:
        hello_count = int(getcf)
        print(hello_count)
    except:
        print('參數不是數字')
        hello_count = 0
    # 監視器觸發次數達設定值時發送訊息
    if hello_count >= 960:
        hello_msg = True
        hello_count = 0
    else:
        hello_msg = False
        hello_count += 1

    wks.update_values("H1", [[str(hello_count)]])

    return hello_msg, hello_count



def msg_txt_specific(msg_specific):
    
    message_all = []
    msgsave = ""
    for i in jspe[msg_specific]:

        if type(i) == str:
            message = TextSendMessage(text=i)
            message_all.append(message)
        elif type(i) == list:
            for g in i:
                msgsave += g + "\n"
            message = TextSendMessage(text=msgsave[:-1])
            message_all.append(message)
        else:
            message = TextSendMessage(text="發生錯誤")
            message_all.append(message)
    return message_all
    



# 必須放上自己的Channel Access Token
line_bot_api = LineBotApi(jdata['TOKEN'])
# 必須放上自己的Channel Secret
handler = WebhookHandler(jdata['SECRET'])
yourID = jdata['YOURID']


@app.route("/", methods=['GET'])
def hello():
    checkmsg, checknum = hello_msg_check()
    if checkmsg == True:  
        line_bot_api.push_message(yourID, TextSendMessage(text='機器人已啟動成功!'))
    
    
    return f"啟動成功 >> {checknum} 次"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'



@handler.add(MessageEvent)
def handle_message(event):
    global password, sayallrecord, usernewsay, saynewtime, bancheck, temppass
    # 時間
    newtoday = datetime.utcnow() + timedelta(hours=8)
    #設定學統測時間
    study_time = datetime(2025, 1, 18, 0)
    system_time = datetime(2025, 4, 26, 0)
    # 用戶id
    usid = event.source.user_id
    print(usid)

    if usid in jban and event.message.text.startswith("s!"):
        if newtoday.strftime('%Y-%m-%d %H:%M:%S') <= jban[usid][1]:
            msg_ban = TextSendMessage(f'*您已被管理員封禁*\n封禁原因:{jban[usid][0]}\n解封日期{jban[usid][1]}')
            line_bot_api.reply_message(event.reply_token, [msg_ban])
            bancheck = False
        elif newtoday.strftime('%Y-%m-%d %H:%M:%S') > jban[usid][1]:
            print("該用戶已被解禁")
            bancheck = True

    if event.message.type == "text" and bancheck == True:
        

        #暫時使用完全符合 必要時將==改為in即可修正為句中包含詞語時回覆
        if "學測" in event.message.text: 
            result = study_time - newtoday
            hour = result.seconds // 3600
            min = result.seconds %3600//60
            message = TextSendMessage(text="距離學測還剩下約{}天{}小時{}分鐘 ".format(result.days, hour, min))
            # message2 = TextSendMessage(text="學測日期是2025年1月17~19日")
            line_bot_api.reply_message(event.reply_token,[message])
            print("回覆學測倒數")

        if "統測" in event.message.text:
            result = system_time - newtoday
            hour = result.seconds // 3600
            min = result.seconds %3600//60
            message = TextSendMessage(text="距離統測還剩下約{}天{}小時{}分鐘 ".format(result.days, hour, min))
            # message2 = TextSendMessage(text="會考日期是2022年5月3~日")
            line_bot_api.reply_message(event.reply_token,[message])
            print("回覆統測倒數")


        if event.message.text in jspe:
            msg_array = msg_txt_specific(event.message.text)
            line_bot_api.reply_message(event.reply_token, msg_array)
            print("發送特定文字出發訊息")
        
        
        if event.message.text.startswith("s!say"):
            reply = event.message.text
            characters = "s!say "
            message = TextSendMessage(text=''.join( x for x in reply if x not in characters))

            line_bot_api.reply_message(event.reply_token,[message])

            print("重複說話")
        

    
       

        # 檢測指令類型
        event_txt = event.message.text
        identity_check = "0"
        admin_check = "f"
        cmd_check = "f"
        cmd_look = "0"
        cmd_pws = "0"
        if event.message.text.startswith("s!"):
            if event_txt.startswith("s!tempacc"):
                evtxt = event_txt.split(" ", 2)
                event_txt = evtxt[2]
                cmd_pws = "t"

            # 管理
            for cmd in ["s!msgdm"]:
                if event_txt.startswith(cmd):
                    print("包含此管理指令")
                    cmd_check = "t"
                    cmd_look = "t"
            # 特殊
            for cmd in ["s!backup", "s!searec", "s!userid", "s!testcmd"]:
                if event_txt.startswith(cmd):
                    print("包含此特殊指令")
                    cmd_check = "t"
                    cmd_look = "v"


            if cmd_check == "t":
                
                if cmd_pws == "t":
                    
                    if evtxt[1] == temppass:
                        print("該用戶使用臨時特殊權限")
                        identity_check = "t"
                    elif evtxt[1] == temppass_admin:
                        print("該用戶使用臨時>管理<權限")
                        identity_check = "t"
                        admin_check = "t"
                    else:
                        print("該用戶使用臨時權限時密碼錯誤")
                        identity_check = "pe"
                    
                elif juser[usid][2] == "admin":
                    print("檢測該用戶為>>管理者")
                    identity_check = "t"
                    admin_check = "t"
                elif juser[usid][2] == "vip":
                    print("檢測該用戶為>>特殊用戶")
                    identity_check = "t"
                elif juser[usid][2] == "user":
                    print("檢測該用戶為>>普通用戶")
                    identity_check = "f"
                else:
                    print("無法確認身份")
                    identity_check = "n"
            else:
                print("不包含此指令")
        
        
        ####################################################################################################
        # 以下為管理指令區
        ####################################################################################################

        if identity_check == "t" and admin_check == "t" and cmd_look == "t":
            

            if event_txt.startswith("s!msgdm"):
                try:
                    msg = event_txt.split(" ")
                    print(msg)
                    user_id = msg[1]
                    message = ""
                    for mg in range(len(msg[2:])):
                        message += msg[2:][mg] + " "
                    
                    try:
                        line_bot_api.push_message(user_id, TextSendMessage(text=message))
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text='>>訊息已發送<<'), TextSendMessage(text=message)])
                    except:
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage('訊息發送失敗\n請確認用戶id和格式是否正確')])
                
                except:
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage('格式錯誤\n請重新檢查格式並重新輸入')])
                print("發送私訊")


        ####################################################################################################
        # 以下為特殊用戶指令區
        ####################################################################################################


        elif identity_check == "t" and cmd_look == "v":
            
            #
            if "s!backup" == event_txt:
                message1 = TextSendMessage('備份中, 請稍候...')
                msgtime = datetime.strftime(newtoday, "%Y年%m月%d日 %H點%M分%S秒")
                message2 = TextSendMessage('備份完成, 備份時間-' + msgtime)
                message3 = TextSendMessage('>>備份網址<<\nhttps://docs.google.com/spreadsheets/d/紀錄檔不公開/edit?usp=sharing')
                
                line_bot_api.reply_message(event.reply_token,[message1,message2,message3])
                
            #
            if event_txt.startswith("s!searec"):
                etxt = event_txt
                
                try:
                    meber_txt = etxt.replace("s!searec ", "")
                    meber = int(meber_txt)
                    mb_type = "int"
                except:
                    try:
                        meber_ord = meber_txt.split("-")
                        if len(meber_ord) >= 3:
                            error_txt = "後面參數應為兩個數字, 請重新輸入"
                            mb_type = "error"
                        elif len(meber_ord) == 2:
                            meber_int = []
                            meber_int.append(int(meber_ord[0]))
                            mb_type = "int"
                            try:
                                meber_int.append(int(meber_ord[1]))
                                mb_type = "ordinal"
                            except:
                                error_txt = "後面參數應為兩個數字, 請輸入正確數值"
                                mb_type = "error"
                        else:
                            error_txt = "後面的參數發生錯誤, 請重新輸入"
                            mb_type = "error" 
                    except:
                        error_txt = '後面的參數錯誤, 請輸入正確數值'
                        mb_type = "error"
                def query_record(meber):
                    gc = pygsheets.authorize(service_file='./goldkey.json')
                    sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/記錄檔不公開/')
                    wks_list = sht.worksheets()
                    print(wks_list)
                    wks = sht[0]
                    bkdf = len(wks.get_all_values())+1
                    shdf = bkdf - meber
                    bkconu = "F" + str(shdf)
                    print(f'{bkdf}\n{shdf}\n{bkconu}')
                    bkmng = str(wks.cell(bkconu))
                    print(bkmng, type(bkmng))
                    bkmsg = bkmng.replace(f"<Cell {bkconu} '", "").replace("'>", "")
                    print(bkmsg)
                    if bkmsg == "text" or bkmsg == "location":
                        bkmconu = "E" + str(shdf)
                        bkmmng = str(wks.cell(bkmconu))
                        msg_txt = bkmmng.replace(f"<Cell {bkmconu} '", "").replace("'>", "")
                        message1 = [msg_txt]
                        mg_type = "txt"
                    else:
                        bkmconu = "G" + str(shdf)
                        geturla = str(wks.cell(bkmconu))
                        print(geturla)
                        geturlb = geturla.replace(f"<Cell {bkmconu} '", "").replace("'>", "")
                        geturl = geturla.replace(f"<Cell {bkmconu} 'https://drive.google.com/file/d/", "").replace("/view?usp=drivesdk'>", "")
                        geturl = 'https://drive.google.com/uc?export=download&id=' + geturl

                        bk_again_coun = "F" + str(shdf)
                        getcf = str(wks.cell(bk_again_coun))
                        bkmg = getcf.replace(f"<Cell {bk_again_coun} '", "").replace("'>", "")
                        print(bkmg)

                        if bkmg == "image":
                            message1 = [geturl]
                            mg_type = "img"
                        elif bkmg.startswith("video"):
                            message1 = [geturlb]
                            mg_type = "vde"
                        elif bkmg.startswith("audio"):
                            audio_s = int(float(bkmg.replace("audio , ", "")) + 1)
                            message1 = [geturl, audio_s]
                            mg_type = "ado"
                    
                    return message1, mg_type
                
                if mb_type == "int":
                    if meber >= 1 and meber <= 50:
                        mg_msg, mg_type = query_record(meber)
                        if mg_type == "txt":
                            message1 = TextSendMessage(text=f"*文本*\n{mg_msg[0]}")
                        elif mg_type == "vde":
                            message1 = TextSendMessage(text=f"*影片*\n{mg_msg[0]}")
                        elif mg_type == "img":
                            message1 = ImageSendMessage(original_content_url=mg_msg[0], preview_image_url=mg_msg[0])
                        elif mg_type == "ado":
                            message1 = AudioSendMessage(original_content_url=mg_msg[0], duration=mg_msg[1])
                    else:
                        message1 = TextSendMessage('後方參數需為1～50')
                elif mb_type == "ordinal":
                    if meber_int[0] == meber_int[1]:
                        if meber_int[0] >= 1 and meber_int[0] <= 50:
                            mg_msg, mg_type = query_record(meber_int[0])
                            if mg_type == "txt":
                                message1 = TextSendMessage(text=f"*文本*\n{mg_msg[0]}")
                            elif mg_type == "vde":
                                message1 = TextSendMessage(text=f"*影片*\n{mg_msg[0]}")
                            elif mg_type == "img":
                                message1 = ImageSendMessage(original_content_url=mg_msg[0], preview_image_url=mg_msg[0])
                            elif mg_type == "ado":
                                message1 = AudioSendMessage(original_content_url=mg_msg[0], duration=mg_msg[1])
                        else:
                            message1 = TextSendMessage('後方參數需為1～50')
                    elif meber_int[0] < meber_int[1]:
                        if meber_int[0] >= 1 and meber_int[1] <= 50:
                            msg1 = "***---***\n"
                            for mbi in range(meber_int[0], meber_int[1]+1, 1):
                                mg_msg, mg_type = query_record(mbi)
                                if mg_type == "txt":
                                    mgt = "*文本*"
                                elif mg_type == "img":
                                    mgt = "*圖片*"
                                elif mg_type == "vde":
                                    mgt = "*影片*"
                                elif mg_type == "ado":
                                    mgt = "*語音*"
                                msg1 += f"{mgt}\n{mg_msg[0]}\n***---***\n"
                            message1 = TextSendMessage(text=msg1)
                        else:
                            message1 = TextSendMessage('後方參數需為1～50')
                    elif meber_int[0] > meber_int[1]:
                        if meber_int[1] >= 1 and meber_int[0] <= 50:
                            msg1 = "***---***\n"
                            for mbi in range(meber_int[0], meber_int[1]-1, -1):
                                mg_msg, mg_type = query_record(mbi)
                                if mg_type == "txt":
                                    mgt = "*文本*"
                                elif mg_type == "img":
                                    mgt = "*圖片*"
                                elif mg_type == "vde":
                                    mgt = "*影片*"
                                elif mg_type == "ado":
                                    mgt = "*語音*"
                                msg1 += f"{mgt}\n{mg_msg[0]}\n***---***\n"
                            message1 = TextSendMessage(text=msg1)
                        else:
                            message1 = TextSendMessage('後方參數需為1～50')
                elif mb_type == "error":
                    message1 = TextSendMessage(text=error_txt)
                else:
                    message1 = TextSendMessage('未知錯誤, 請重新輸入')
                line_bot_api.reply_message(event.reply_token,[message1])

            #
            if event_txt.startswith("s!userid"):
                try:
                    msg = event_txt.split(" ")
                    print(msg)
                    usn_type = msg[1]
                    if usn_type == "all":
                        usn_name = ""
                        for userid in juser:
                            usn_name += f">>><<<\n{userid}\n{juser[userid][0]}\n"
                        usn_name += "->結束<-"
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=usn_name)])
                    elif usn_type == "search":
                        usnname = ""
                        for mg in range(len(msg[2:])):
                            usnname += msg[2:][mg] + " "
                            usnname = usnname[:-1]
                        usnid = "<<------>>\n"
                        for key, value in juser.items():
                            if usnname in value[0]:
                                usnid += f'{key}\n{value[0]}\n<<------>>\n'
                            elif usnname in value[1]:
                                usnid += f'{key}\n{value[0]}\n{value[1]}\n(此資料可能有誤)\n<<------>>\n'
                        if usnid == "<<------>>\n":
                            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text='查無資料')])
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text='查詢到資料為'), TextSendMessage(text=usnid)])
                    elif usn_type == "id":
                        usn_id = msg[2]
                        try:
                            prof = line_bot_api.get_profile(usn_id)
                        except:
                            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="ID有誤")])
                        pname = prof.display_name
                        pstat = prof.status_message
                        plang = prof.language
                        pimg = prof.picture_url
                        imgmsg = ImageSendMessage(original_content_url=pimg, preview_image_url=pimg)
                        pmsg = f"使用者名稱：{pname}\n使用者狀態消息：{pstat}\n使用者偏好語言{plang}\n使用者使用者頭像圖片："
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=pmsg), imgmsg])
                    else:
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text='輸入類型錯誤\n請重新輸入')])
                except:
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text='格式錯誤\n請重新檢查格式並重新輸入')])
                print("查詢id")

            #
            if event_txt.startswith("s!testcmd"):
                pass

        
        ####################################################################################################
        # 以下為權限不足
        ####################################################################################################
        elif identity_check == "t" and cmd_look == "t" and admin_check == "f":
            line_bot_api.reply_message(event.reply_token, [TextSendMessage('權限不足, 無法使用該指令')])
        elif identity_check == "f":
            line_bot_api.reply_message(event.reply_token, [TextSendMessage('權限不足, 無法使用該指令')])
        elif identity_check == "n":
            line_bot_api.reply_message(event.reply_token, [TextSendMessage('未知身份, 無法使用該指令')])
        elif identity_check == "pe":
            line_bot_api.reply_message(event.reply_token, [TextSendMessage('密碼錯誤, 無法啟用臨時權限')])


        



    
    # 時間
    newtoday = datetime.utcnow() + timedelta(hours=8)
    saynewtime = datetime.strftime(newtoday, "%Y年%m月%d日 %H點%M分%S秒")
    

    
    print("開始紀錄")


    try:
        profile = line_bot_api.get_profile(usid)
        
    except LineBotApiError as e:
        profile = '無資料'
    print(profile)
    
    
    # 備註預設
    newurl = ''
    
    # 文字紀錄
    if event.message.type == "text":
        rcid = event.message.text
        idtype = 'text'

    # 圖片id紀錄
    if event.message.type == "image":
        rcid = event.message.id
        idtype = 'image'
        newurl = fileupdata(rcid, idtype)

    # 影片id紀錄
    if event.message.type == "video":
        rcid = event.message.id
        rcvtime = str(event.message.duration / 1000)
        print("此音訊有" + rcvtime + "秒")
        idtype = 'video , ' + rcvtime
        vatype = 'video'
        newurl = fileupdata(rcid, vatype)

    # 音訊id紀錄
    if event.message.type == "audio":
        rcid = event.message.id
        rcatime = str(event.message.duration / 1000)
        print("此音訊有" + rcatime + "秒")
        idtype = 'audio , ' + rcatime
        vatype = 'audio'
        newurl = fileupdata(rcid, vatype)


    # 位置id紀錄
    if event.message.type == "location":
        rcaddress = event.message.address # 位置地址
        rclongi = event.message.longitude # 位置經度
        rclati = event.message.latitude # 位置緯度
        
        rcid = rcaddress + " , 緯經度" + str(rclati) + ", " + str(rclongi) #緯度, 經度
        idtype = 'location'

    



    try:
        username = profile.display_name
    except:
        try:
            username = juser[profile.display_name[1]]
        except:
            username = '無資料'
    try:
        userpic = profile.picture_url
    except:
        userpic = '無資料'

    if username == '無資料':
        if usid in juser:
            username = juser[usid][0]
        else:
            username = '無資料, 不在字典中'
            print('不在字典中')
    
    

    print(username)
    print(userpic)
        
    etrcon = [usid, username, userpic, saynewtime, rcid, idtype, newurl]

    gc = pygsheets.authorize(service_file='./goldkey.json')
    sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1TjbpD1ba9n7n7MnZTNE_siGwqswYH7PgCNscEVvbeWw/')
    wks_list = sht.worksheets()
    print(wks_list)
    wks = sht[0]
    wks.update_values('A1', [['用戶id', '用戶名稱', '用戶頭像網址', '時間', '訊息id或文字', 'id格式', '備註>>保持在線計數']])

    df = len(wks.get_all_values())+1
    print(df)

    conu = "A" + str(df)
    print(conu)
    wks.add_rows(1)
    print(etrcon)
    wks.update_values(conu, [etrcon])

    print("紀錄結束")





if __name__ == "__main__":
    sched.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
