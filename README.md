# easy_crop_diseases
本项目使用Python-Flask搭建了服务器。
data文件夹中存放农作物病虫害分类模型；work文件夹中存放项目文件。
运行环境：Windows，Python3
## 1、安装requirements.txt文件中的Python第三方库
进入work文件夹，命令行运行 pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
## 2、创建数据库，用于存放历史记录
进入work文件夹，命令行运行python create_table.py
## 3、启动服务器
进入work文件夹，命令行运行python app_server.py dev
