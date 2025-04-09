# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from dotenv import load_dotenv  
import os
import random     
import shelve
from datetime import datetime,timedelta
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

#临时设置，阿里云短信服务秘钥
load_dotenv()  
ALIBABA_CLOUD_ACCESS_KEY_ID= os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
ALIBABA_CLOUD_ACCESS_KEY_SECRET=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')


class login:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Dysmsapi20170525Client:
        """
        使用AK&SK初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考。
        # 建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html。
        config = open_api_models.Config(
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID。,
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Dysmsapi
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    @staticmethod
    def send_verification_code(
        phone_numbers: str
    ) -> None:
        client = login.create_client()
        verification_code = random.randint(1000, 9999)
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers =str(phone_numbers),
            sign_name='小邮智慧学伴',
            template_code='SMS_471285404',
            template_param = f'{{"code":"{verification_code}"}}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            client.send_sms_with_options(send_sms_request, runtime)
            with shelve.open('verification_codes.db') as db:
                 db[phone_numbers] = {'code': verification_code, 'timestamp': datetime.now()}

        except Exception as error:
            print(error)


    def verify_code(self, phone_number, code):  
        # 假设 phone_number 是一个字符串  
        with shelve.open('verification_codes.db') as db:  
            # 检查电话号码是否在数据库中  
            if phone_number in db:  
                data = db[phone_number]  
                # 检查验证码是否匹配且未过期（5分钟） 
                # print(data['code']) 
                # print(type(data['code']))
                # print(data['timestamp'])
                # print((datetime.now() - data['timestamp']).total_seconds())
                # print(timedelta(minutes=5).total_seconds())
                # print(type(code))
                if str(data['code']) == code and (datetime.now() - data['timestamp']).total_seconds() <= timedelta(minutes=5).total_seconds():  
                    return 1  # 验证码匹配且未过期  
                else:  
                    return 0
            else:  
                return 0
       
