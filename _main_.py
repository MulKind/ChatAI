import os
import requests  
import json  
from flask import Flask , request ,jsonify,flash,redirect
from flask_cors import CORS  # type: ignore
from chain import RAG
from phone_number_login import login
import pymysql

# 数据库连接  
config = {  
    'host': '192.168.0.220',  # 数据库主机地址
    'user': 'root',  # 数据库用户名
    'password': 'root',  # 数据库密码
    'db': 'xiaoyou',  # 数据库名
    'port': 8808,
    'charset': 'utf8mb4',  # 字符集 
    'cursorclass': pymysql.cursors.DictCursor  # 使用字典游标，使得查询结果以字典形式返回  
}  


# 建立数据库连接
  
connection=pymysql.connect(**config)  # 使用**config将字典展开为关键字参数传递给connect函数  
UPLOAD_FOLDER = '/home/klind/桌面/ChatAI/UPLOAD_FOLDER'
RAG=RAG()   
login=login()
app = Flask(__name__) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
CORS(app,resources=r'/*')


# # #登录部分
# # 发送验证码
@app.route('/send_verification_code', methods=['POST'])
def  send_verification_code() :
     data = request.json
     phone_numbers=  data.get("phone_numbers")
     try:  
    # 创建游标对象  
        with connection.cursor() as cursor:  
            # 编写SQL查询语句  
            sql = "SELECT * FROM login WHERE phone_numbers = %s"  
            # 执行查询  
            cursor.execute(sql, (phone_numbers,))  
            # 获取查询结果  
            result = cursor.fetchone()  
          
        # 判断是否找到手机号  
        if result:  
            print(f"找到手机号: {phone_numbers}")
            return jsonify({"code": 400, "error": "手机号已经注册过"}), 400
        else:
            # login.send_verification_code(phone_numbers)
            debug = login.send_verification_code(phone_numbers)
            return jsonify({"code": 200, "message": "验证码发送成功", "Debug": str(debug)}), 200
     except Exception as e:
        return jsonify({"code": 500, "error": str(e)}), 500  

#验证码校验并添加用户
@app.route('/verify_code', methods=['POST'])
def verify_code():
     data = request.json
     phone_numbers=  data.get("phone_numbers")
     code=data.get("code")
     username=data.get("username")
     password=data.get("password")
     print(phone_numbers,code,username,password)
     result=login.verify_code(phone_numbers,code)
     print(result)
     if result==1:
         print("111111111111")
         try:  
            with connection.cursor() as cursor:  
                # 创建SQL插入语句  
                sql = "INSERT INTO login (phone_numbers, username, password) VALUES (%s, %s, %s)"  
                # 执行SQL语句  
                cursor.execute(sql, (phone_numbers,username, password))  
        
            # 提交事务  
            connection.commit()  
        
            print("记录插入成功")
            return jsonify({"code": 200, "message": "注册成功"}), 200
        
         except pymysql.MySQLError as e:  
            print(f"插入记录时发生错误: {e}")
            return jsonify({"code": 500, "error": str(e)}), 500 
     else:
       return jsonify({"code": 400, "error": "验证码错误或已过期"}), 400



##登录##
@app.route('/login/login', methods=['POST'])
def login_login():
    if request.method == "POST":
        data = request.json
        
        phone_number =  data.get("phone_numbers")
        password =  data.get("password")
        with connection.cursor() as cursor:
            # cursor.execute("select id,username,role,ctime,phone_numbers from login where phone_numbers=\""
            #                +str(phone_numbers)+"\" and password=\""+str(password)+"\"")
            cursor.execute("select id,username,role,ctime,phone_numbers from login where phone_numbers = %s and password = %s", (phone_number, password))
            data = cursor.fetchone()
        if(data!=None):
            print("result:",data)
            return jsonify({"code": 200, "username": str(data['username'])})
        else:
            print("result: NULL")
            return jsonify({"code": 401, "error": "登录失败，手机号或密码错误"}), 401
        
        
#修改密码
@app.route('/login/update', methods=['POST'])
def login_update():
    if request.method == "POST":
        data = request.json
        phone_numbers = data.get("phone_numbers")        
        new_password = data.get("new_password")
        old_password = data.get("old_password")
        try:
            with connection.cursor() as cursor:  
                # 使用参数化查询来防止SQL注入  
                sql = "UPDATE login SET password=%s WHERE phone_numbers=%s"
                sql2 = "SELECT password FROM login WHERE phone_numbers=%s"
                cursor.execute(sql2, phone_numbers)
                aa = cursor.fetchone()
                if old_password == aa['password']:
                    cursor.execute(sql, (new_password, phone_numbers))
                    connection.commit()
                else:
                    print("An error occurred")
                    return jsonify({'code': '301', 'message': '旧密码错误'})
            print("update password successfully!")
            return jsonify({'code': '200', 'message': '修改密码成功!'})
        except Exception as e:
            print("update password failed:",e)
            connection.rollback() #发生错误就回滚
            return jsonify({'code': '500', 'message': '修改密码失败', 'error': str(e)})
# ##############################################################################################
#对话
@app.route('/conversation', methods=['POST'])  
def ask_question():  
    data = request.json  
    question = data.get('question')  
    phone_numbers=data.get('phone_numbers')  
    try:  
        answer = RAG.conversation(question, phone_numbers)  
        return jsonify({'code': '200', 'answer': answer}), 200   
    except Exception as e:  
        return jsonify({'code': '500', 'message': '获取回答失败', 'error': str(e)})


#上传文件到数据库，txt
@app.route('/upload', methods=['POST'])  
def upload_file():  
    if request.method == 'POST':  
        # 检查是否有文件在请求中  
        if 'file' not in request.files:  
            flash('No file part')  
            return redirect(request.url)  
        file = request.files['file']  
        # 如果用户没有选择文件，浏览器也会提交一个没有文件名的空部分  
        if file.filename == '':  
            flash('No selected file')  
            return redirect(request.url)  
        if file: 
            filename = file.filename  
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)  
            file.save(filepath)  
            RAG.upload(filepath)
            return f'File {filename} uploaded successfully'  
    return '''  
    <!doctype html>  
    <title>Upload new File</title>  
    <h1>Upload new File</h1>  
    <form method=post enctype=multipart/form-data>  
      <input type=file name=file>  
      <input type=submit value=Upload>  
    </form>  
    '''  


if __name__ == '__main__':     
   app.run(host='0.0.0.0', port=55555)  
   connection.close()  
   print("结束")



