# encoding: utf-8
"""
python server for multi-thread paddle predict
based on flask and twisted
"""
import init_paths
import time
import ctypes
import json
import pymysql
import conf.server_conf

from utils.logger_util import logger
from conf.server_conf import config
from utils.pivot import Pivot

from flask import Flask
from flask import jsonify
from flask import abort
from flask import request
from flask import make_response
import sys

# get main version of python, maybe 3 or 2
PYTHON_VERSION = int(sys.version.split('.')[0])
EXECUTOR = 'executor'
PREDICTOR = 'predictor'
app = Flask(__name__)

# connect mysql
database = pymysql.connect(host="localhost",user='root',passwd='root',db='planteye')
cursor = database.cursor()

class ApiResult(object):
    """
    API 返回结果
    """
    log_id = int
    error_code = int
    errpr_message = str
    data = dict

    def __init__(self, code=0, log_id=None, message='', data=None):
        self.log_id = log_id
        self.error_code = code
        self.error_message = message
        self.data = data
        self.top3 = None
    def success(self, data=None):
        """成功返回值"""
        # self.data = data
        dic = {i:'%.2f'%data['result'][i] for i in range(len(data['result']))}
        sort_dic = sorted(dic.items(), key=lambda d:d[1], reverse = True)
        print(sort_dic[:3])
        self.top3 = sort_dic[:3]

    def error(self, code=-1, message='error', data=None):
        """失败返回值"""
        self.error_code = code
        self.error_message = message
        self.data = data


@app.route('/getimg', methods=['get'])
def get_img():
    user_id = 1
    img_id = 1
    sql = "select img from record where user_id={} and id={};".format(user_id,img_id)
    cursor.execute(sql)
    database.commit()
    img = cursor.fetchone()[0]
    return img


@app.route('/record', methods=['get'])
def get_record():
    user_id = 1
    sql = "select id,label,score from record where user_id={};".format(user_id)
    cursor.execute(sql)
    records = cursor.fetchall()
    database.commit()
    record_list = [{index:i} for index,i in enumerate(records)]
    return json.dumps(record_list)


@app.route('/infer', methods=['POST'])
def recognize():
    """
    处理post请求,并返回处理后的结果
    """
    # print(request.headers)
    # print(request.form)
    file = request.files['imgfile']
    # print(file, file.filename)
    # with open('receiveimg.jpg', 'wb') as f:
    #     f.write(file.stream.read())
    if not request.form:
        abort(400)
    if 'log_id' in request.form:
        log_id = request.form['log_id']
        logger.set_logid(str(log_id))
    else:
        logger.set_auto_logid()
        log_id = logger.get_logid()
    log_id = int(log_id)
    result = ApiResult(log_id=log_id)
    start_time = time.time()

    try:
        image_bytes = file.stream.read()
        task_data = process_data(image_bytes)
        # print(task_data.shape)
        start_time = time.time()
        max_request_time = float(config.get('max_request_time'))
        index = pivot.set_task_queue(task_data, max_request_time)
        if index is not None:
            pred = pivot.get_result_list(index)
            pred['log_id'] = log_id
            result.success(data=pred)
            # 历史记录入库
            label,score,user_id = result.top3[0][0],result.top3[0][1],1
            sql = "insert into record(img,label,score,user_id) values (%s,{},{},{});".format(label,score,user_id)
            print(result.top3[0][0],result.top3[0][1])
            cursor.execute(sql,args=(image_bytes))
            database.commit()
        else:
            result.error(message="busy, wait then retry")
    except Exception as err:
        logger.error("infer exception: {}".format(err))
        result.error(message=str(err))

    period = time.time() - start_time
    logger.info("request cost:{}".format("%2.2f sec" % period))
    return json.dumps(result, default=lambda o: o.__dict__)


@app.route('/')
def index():
    """
    访问root
    """
    logger.info("visit root page")
    return 'Index Page'


@app.route('/state')
def state():
    """
    访问state
    """
    logger.info("visit state page")
    return '0'


@app.errorhandler(404)
def not_found(error):
    """
    如果访问出错，返回404错误
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    """
    web server start
    """

    if len(sys.argv) < 2:
        logger.critical("too less argv, need a start profile, run as: python app_server.py dev")
        exit(1)
    else:
        conf.server_conf.ServerConfig.init_evn(sys.argv[1])

        infer_type = config.get('predictor_or_executor')

        from twisted.internet import reactor
        from twisted.web.resource import Resource
        from twisted.web.server import Site
        from twisted.web.wsgi import WSGIResource
        from utils.consumer import InferConsumer
        from business_service import process_data

        pivot = Pivot(int(config.get("max_task_num")))
        infer_consumer = InferConsumer(pivot, float(config.get("max_get_time")))
        port = int(config.get("flask.server.port"))
        work_thread_count = int(config.get('work.thread.count'))
        site_root = str(config.get('server.root.site'))

        reactor.suggestThreadPoolSize(int(work_thread_count))
        flask_site = WSGIResource(reactor, reactor.getThreadPool(), app)
        root = Resource()
        root.putChild(site_root if PYTHON_VERSION == 2 else bytes(site_root, encoding='utf-8'), flask_site)
        logger.info("start app listen port:{} thread pool size:{} site root:{}"
                    .format(port, work_thread_count, site_root))
        reactor.listenTCP(port, Site(root))

        # 把主线程设置为infer_consumr的守护线程，如果主线程结束了，infer_consumer线程就跟着结束
        infer_consumer.setDaemon(True)
        infer_consumer.start()

        reactor.run()

