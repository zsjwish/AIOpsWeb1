import csv
import json
import os

# Create your views here.
import time
from datetime import datetime as datet
import datetime

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection

from AIOps_pro.static_value import sv
from db.mysql_operation import query_model_info, query_abnormal_list, insert_abnormal_list, \
    update_one_label_for_dataset, update_batch_label_for_dataset
from isolate_model.base_function import save_datas_with_labels, use_XGBoost_predict, train_model, get_datas_for_tag, \
    update_datas_for_tag, predict_future_30, print_model


def index(request):
    return render(request, 'models/main.html')


def menu(request):
    return render(request, 'models/menu.html')


def hello(request):
    return render(request, 'models/hello.html')


def success(request):
    return render(request, 'models/upload_success.html')


def submit(request):
    # 判断接收的值是否为POST
    print(request.body.decode())
    print(type(request.body.decode()))
    if request.method == "POST":
        body = json.loads(request.body.decode())
        result = use_XGBoost_predict(body)
        if result == 1:
            model_name = body["host_id"]
            times = datet.strptime(body["time"], '%Y-%m-%d %H:%M:%S')
            value = float(body["kpi"])
            insert_abnormal_list(model_name, times, value)
        print(result)
        return HttpResponse(result, content_type = "application/json")
    return render(request, 'models/upload_one_data.html')


def reset_xgboost_model(request):
    kind = "XGBoost"
    data_name = request.POST["data_name"]
    sv.executor5.submit(train_model, kind, data_name, 1)


def reset_lstm_model(request):
    kind = "LSTM"
    data_name = request.POST["data_name"]
    sv.executor5.submit(train_model, kind, data_name, 1)


def train(request):
    """
    用于训练数据
    :param request:
    :return:
    """
    # redis连接池
    redis_conn = get_redis_connection("default")
    # 获取data_set_name数据集名称并返回str的list表
    data_name = redis_conn.smembers("data_set_name")
    dataset = {"names": [i.decode for i in data_name]}
    # 判断接收的值是否为POST
    if request.method == "POST":
        kind = request.POST["kind"]
        data_name = request.POST["data_name"]
        # data_name是文件名
        info = {"kind": kind, "data_name": data_name}
        sv.executor5.submit(train_model, kind, data_name)
        # executor5.shutdown(wait = False)
        print("overoverover")
        # if res == 0:
        #     return render(request, 'models/model_exists.html')
        time.sleep(1.5)
        # return render(request, 'models/train_success.html', context = info)
    return render(request, 'models/train_model.html', context = dataset)


def xgboost_model_info(request):
    # if request.method == 'POST':
    res = query_model_info("XGBoost")
    return render(request, 'models/xgboost_model_info.html', {"datas": res})
    # return render(request, 'models/test.html', {"datas": res})


def lstm_model_info(request):
    # if request.method == 'POST':
    res = query_model_info("LSTM")
    return render(request, 'models/lstm_model_info.html', {"datas": res})




def tag(request):
    """
    对数据标注
    :param request:
    :return:
    """
    # 判断接收的值是否为POST
    redis_conn = get_redis_connection("default")
    data_name = redis_conn.smembers("data_set_name")
    info = dict(data_names = [i.decode for i in data_name])
    time_now = datetime.datetime.now()
    timeformat = '%Y-%m-%d %H:%M'
    info["start_time"] = (time_now - datetime.timedelta(hours = 1)).strftime(timeformat)
    info["end_time"] = time_now.strftime(timeformat)
    print(info)
    if request.method == "POST":
        info["table_name"] = request.POST["data_name"]
        info["start_time"] = request.POST["start_time"]
        info["end_time"] = request.POST["end_time"]
        info["label"] = int(request.POST["label"])
        info["name"] = request.POST["data_name"]
        print(info)
        info["datas"] = update_datas_for_tag(table_name = info["table_name"], start_time = info["start_time"],
                                             end_time = info["end_time"], label = info["label"])
        print(info)
        return render(request, 'models/tag.html', context = info)
    return render(request, 'models/tag.html', context = info)


def model_info(request):
    """
    查看模型信息
    :param request:
    :return:
    """
    info = {"kind": "XGBoost"}
    if request.method == 'POST':
        kind = request.POST["kind"]
        res = query_model_info(kind)
        print(type(res))
        return render(request, 'models/models_list.html', {"kind": kind,
                                                           "datas": res})
    return render(request, 'models/models_list.html', context = info)


def abnormal(request):
    """
    查看模型信息
    :param request:
    :return:
    """
    info = dict()
    time_now = datetime.datetime.now()
    timeformat = '%Y-%m-%d %H:%M'
    # info["start_time"] = (time_now - datetime.timedelta(days = 60)).strftime(timeformat)
    # info["end_time"] = time_now.strftime(timeformat)
    info["start_time"] = "2019-03-19T22:10"
    info["end_time"] = "2019-04-29T22:10"
    if request.method == "POST" and (max(len(request.POST["start_time"]),len(request.POST["end_time"])) != 0):
        info["start_time"] = request.POST["start_time"]
        info["end_time"] = request.POST["end_time"]
    print(info["start_time"])
    print(info["end_time"])
    res = query_abnormal_list(info["start_time"], info["end_time"])
    print(type(res))
    info["datas"] = res
    print(info)
    return render(request, 'models/abnormal_list.html', context = info)


def predict(request):
    """
    对数据标注
    :param request:
    :return:
    """
    # 判断接收的值是否为POST
    redis_conn = get_redis_connection("default")
    lstm_name = redis_conn.smembers("lstm_name")
    info = {"data_names": [i.decode for i in lstm_name]}
    if request.method == "POST":
        data_name = request.POST.get("model_name")
        predict_xAxis, predict_value = predict_future_30(data_name)
        datas = {"predict_table": data_name, "predict_xAxis": predict_xAxis, "predict_value": predict_value}
        datas = JsonResponse(datas)
        print("infofffff", datas.getvalue())
        return HttpResponse(datas)
    return render(request, 'models/predict.html', context = info)


@csrf_exempt
def upload(request):
    """
    上传csv文件，注意文件要以host_id uuid形式命名，文件放到file文件夹下, 并且解析存储到数据库中
    :param request:
    :return:
    """
    # 判断接收的值是否为POST
    if request.method == "POST":
        abnormal_rate = request.POST["abnormal_rate"]
        print(abnormal_rate)
        # 上传文件的接收方式应该是request.FILES
        inp_files = request.FILES
        # 通过get方法获取upload.html页面提交过来的文件
        file_obj = inp_files.get('f1')
        if file_obj is None:
            time.sleep(200)
            return render(request, 'models/upload_dataset.html')
            # return render(request, 'models/upload_csv.html', context = {"error_message": "请选择文件后再上传！"})
        # 文件存储路径
        file_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/file/' + file_obj.name
        print(file_path)
        # 将客户端上传的文件保存在服务器上，一定要用wb二进制方式写入，否则文件会乱码
        f = open(file_path, 'wb+')
        # 获取上传的文件名
        f_name = f.name
        print(f_name)
        # 通过chunks分片上传存储在服务器内存中,以64k为一组，循环写入到服务器中
        for line in file_obj.chunks():
            f.write(line)
        f.close()

        if save_datas_with_labels(f_name, float(abnormal_rate)):
            pass
            # return render(request, 'models/upload_success.html', {'file_name': f_name.split("/")[-1]})
        # return render(request, 'models/upload_failed.html')
        time.sleep(200)
    return render(request, 'models/upload_dataset.html')  # 将处理好的结果通过render方式传给upload.html进行渲染


def dashboard(request):
    pass
    return render(request, 'models/dashboard.html', locals())


def test(request):
    # if request.method == 'POST':
    res = query_model_info("XGBoost")
    return render(request, 'models/test.html', {"datas": res})
    # return render(request, 'models/test.html', {"datas": res})


def fixed(request):
    return render(request, 'models/fixed.html')


def data_tag(request):
    # 判断接收的值是否为POST
    redis_conn = get_redis_connection("default")
    data_name = redis_conn.smembers("data_set_name")
    info = dict(data_names = [i.decode for i in data_name])
    time_now = datetime.datetime.now()
    time_format = '%Y-%m-%dT%H:%M'
    # info["start_time"] = (time_now - datetime.timedelta(hours = 1)).strftime(time_format)
    # info["end_time"] = time_now.strftime(time_format)
    info["start_time"] = "2019-02-25T14:10"
    info["end_time"] = "2019-02-25T14:40"
    if request.method == "POST":
        print("1111111111111", request.POST)
        tag = {"table_name": request.POST["table_name"], "start_time": request.POST["start_time"],
               "end_time": request.POST["end_time"], "label": request.POST["label"]}
        print(tag)
        info.update(tag)
        print("info", info)
        if request.POST["kind"] == "change":
            info["datas"] = update_datas_for_tag(table_name = "MSMQ入.csv", start_time = info["start_time"],
                                                 end_time = info["end_time"], label = info["label"])
        else:
            info["datas"] = get_datas_for_tag(table_name = "MSMQ入.csv", start_time = info["start_time"],
                                              end_time = info["end_time"], label = info["label"])
        return render(request, 'models/data_tag.html', context = info)

        # print("1111111111111", request.POST)
        # info["table_name"] = request.POST["table_name"]
        # info["start_time"] = request.POST["start_time"]
        # info["end_time"] = request.POST["end_time"]
        # print("info", info)
        # datas = get_datas_for_tag(table_name = info["table_name"], start_time = info["start_time"],
        #                                   end_time = info["end_time"])
        # print("infoffffffffffffff", datas)
        # datas = JsonResponse(datas, safe=False)
        # print("infofffff", datas.getvalue())
        # return HttpResponse(datas)
    return render(request, 'models/data_tag.html', context = info)


def update_one_label(request):
    """
    单个数据标签重置
    :param request:
    :return:
    """
    data_set_name = request.POST["data_set_name"]
    id = request.POST["id"]
    label_value = request.POST["label_value"]
    result = update_one_label_for_dataset(data_set_name, id, label_value)
    return HttpResponse(result, content_type = "application/json")


def update_batch_label(request):
    """
    批量数据标签重置
    :param request:
    :return:
    """
    data_set_name = request.POST["data_set_name"]
    id = request.POST["id"]
    label_value = request.POST["label_value"]
    result = update_batch_label_for_dataset(data_set_name, id, label_value)
    return HttpResponse(result, content_type = "application/json")