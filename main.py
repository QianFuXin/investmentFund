# encoding:utf-8
import time
import re
import logging

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
import requests
import pandas as pd
import os
import numpy as np
import matplotlib as mpl

# 设置字体
mpl.rcParams['font.sans-serif'] = ['KaiTi']
mpl.rcParams['font.serif'] = ['KaiTi']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

# 文件名称
fileName = f'基金排行{time.strftime("%Y%m%d", time.localtime())}.txt'


# 获取所有基金数据
def getFundData():
    # 存放所有的数据
    allData = []
    pi = 1
    # 开始和结束时间
    today = time.strftime("%Y-%m-%d", time.localtime())
    while 1:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            'Referer': 'http://fund.eastmoney.com/data/fundranking.html'
        }
        logging.info(f"爬取第{pi}页")
        url = f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={today}&ed={today}&qdii=&tabSubtype=,,,,,&pi={pi}&pn=50&dx=1"
        # 表示礼貌
        time.sleep(3)
        try:
            tempData = requests.get(url, headers=headers, timeout=10).text.strip()
            result = re.findall("\[.*\]", tempData)
            if len(result) == 1 and not result[0] == [404]:
                data = eval(result[0])
                # 数据爬取完成，退出循环
                if not data:
                    break
                logging.info(f"第{pi}页数据已爬取完成")
            else:
                logging.info("数据无效，重新爬取。")
                continue
        except Exception  as e:
            logging.error(f"发生了错误：{e}")
            continue
        # 添加本页数据
        allData.extend(data)
        pi += 1
    # 保存数据到本地
    with open(fileName, mode='w', encoding="utf-8") as  file:
        file.write("\n".join(map(str, allData)))


# 进行统计
def recommendFund():
    """
        一支好且稳定基金的标准
        月收益<3月收益<6月收益<1年收益
    """
    columns = ['基金代码', '基金简称', '字符代码', '日期',
               '单位净值', '累计净值', '日增长率', '近1周',
               '近1月', '近3月', '近6月', '近1年',
               '近2年', '近3年', '今年来',
               '成立来']
    df = pd.DataFrame([i.strip().split(",")[:16] for i in allData], columns=columns)
    df = df.set_index("基金代码")
    # 删除一些列
    del df["成立来"]
    del df["今年来"]
    del df["单位净值"]
    del df["累计净值"]
    del df["日增长率"]
    del df["近3年"]
    del df["近2年"]
    del df["近1周"]
    # 将空白值替换为缺失值
    df.replace(to_replace=r'^\s*$', value=np.nan, regex=True, inplace=True)
    # 去除缺失值
    df = df.dropna(subset=['日期', '近1月', '近3月', '近6月', '近1年'])
    # 更改类型
    df["近1月"] = df["近1月"].astype("float")
    df["近3月"] = df["近3月"].astype("float")
    df["近6月"] = df["近6月"].astype("float")
    df["近1年"] = df["近1年"].astype("float")
    # 去除负数据
    df.query("(近1月>0) and (近3月>0) and (近6月>0) and  (近1年>0)", inplace=True)
    # 稳定基金查询
    df.query("(近3月>=近1月) and (近6月>=近3月) and (近1年>=近6月)", inplace=True)
    # 按照近一年的标准进行排序
    df = df.sort_values(by=["近1年"], ascending=False)[:20]
    # 作图
    fig, ax = plt.subplots(figsize=(35, 40))
    df[['近1月', '近3月', '近6月', '近1年']].plot.bar(subplots=True, ax=ax, rot=0)
    # 保存
    fig.savefig(f"{fileName}推荐.png", quality=10)


if __name__ == '__main__':
    # 优先使用本地数据，因为一天之内，这个数据几乎不会有改动。
    if os.path.exists(fileName):
        logging.info("导入本地数据")
        with open(fileName, mode='r', encoding="utf-8") as  file:
            allData = file.readlines()
    else:
        logging.info("开始爬取数据")
        getFundData()
        logging.info("数据爬取已结束")
    recommendFund()
