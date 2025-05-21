# 記錄訊息
def fileupdata(rcid, idtype):

    
    import os
    import os.path
    import json
    from linebot import LineBotApi

    # 轉圖片
    from PIL import Image
    from io import BytesIO
    



    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseUpload
    

    SCOPES = ['https://www.googleapis.com/auth/drive']
    vice_file = ''
    # 檔案型態初始設定
    if idtype == 'image':
        filetype = 'image/png'
        vice_file = '.png'
    elif idtype == 'video':
        filetype = 'video/mp4'
        vice_file = '.mp4'
    elif idtype == 'audio':
        filetype = 'audio/mpeg'
        vice_file = '.mp3'

    # 檔案暫存用
    file_byte = b''
    # 上傳後檔案名稱設定
    filename = f"{idtype} - {rcid}" + vice_file
    # 初始化空圖片字節流
    filedata = BytesIO()



    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    with open('setting.json','r', encoding='utf8') as jfile:
        jdata = json.load(jfile)


    line_bot_api = LineBotApi(jdata['TOKEN'])

    message_content = line_bot_api.get_message_content(rcid)
    for chunk in message_content.iter_content():
        file_byte = file_byte + chunk
    print(file_byte)
    if idtype == 'image':
        file_str = BytesIO(file_byte)
        file_img = Image.open(file_str)
        file_img.save(filedata, format('PNG'))
    elif idtype == 'video':
        file_str = BytesIO(file_byte)
        filedata = file_str
    elif idtype == 'audio':
        file_str = BytesIO(file_byte)
        filedata = file_str
        


    try:
        service = build("drive", "v3", credentials=creds)

        response = service.files().list(
            q="name='ymshlinebot' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute()

        if not response['files']:
            file_metadata = {
                "name": "ymshlinebot",
                "mimeType": "application/vnd.google-apps.folder"
            }

            file = service.files().create(body=file_metadata, fields="id").execute()
            folder_id = file.get('id')
        
        else:
            folder_id = response['files'][0]['id']

        
        file_metadata = {
            "name": filename,
            "parents": [folder_id]
        }

        media = MediaIoBaseUpload(filedata, mimetype=filetype)
        upload_file = service.files().create(body=file_metadata, media_body=media, fields="webViewLink, id").execute()
        newurl = upload_file.get('webViewLink')
        print("Backed up file: " + filename)
        return newurl




    except HttpError as e:
        print("Error: " + str(e))



