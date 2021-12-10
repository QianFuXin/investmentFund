# encoding:utf-8
import time
import logging
import re
from ast import literal_eval
from requests.exceptions import ProxyError, ReadTimeout, ConnectTimeout
from urllib3.exceptions import ReadTimeoutError
from utils.webworm.HeaderAndProxies import *
import requests
import pandas as pd
import os
import numpy as np
import matplotlib as mpl

mpl.rcParams['font.sans-serif'] = ['KaiTi']
mpl.rcParams['font.serif'] = ['KaiTi']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

fileName = f'基金排行{time.strftime("%Y%m%d", time.localtime())}.txt'
allData = []


def getFundData():
    pi = 1
    stopTime = time.strftime("%Y-%m-%d", time.localtime())

    beginTime = f"{int(stopTime[:4]) - 1}-01-01"
    while 1:
        headers = {
            'User-Agent': getRandomAgent(),
            'Referer': 'http://fund.eastmoney.com/data/fundranking.html'
        }
        proxies = getRandomProxies()
        logging.info(f"爬取第{pi}页")
        url = f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=qjzf&st=desc&sd={beginTime}&ed={stopTime}&qdii=&tabSubtype=,,,,,&pi={pi}&pn=50&dx=1"
        try:
            data = requests.get(url, headers=headers, proxies=proxies, timeout=3).text.strip()
        except ProxyError:
            logging.warning("代理无效")
            continue
        except (ReadTimeout, ConnectTimeout, ReadTimeoutError):
            logging.warning("代理超时")
            continue
        except Exception  as e:
            logging.error(f"其他错误{e}")
            continue
        try:
            data = re.findall("\[.*\]", data)[0]
            temp = literal_eval(data)
            logging.error(data[:20])
        except:
            logging.warning("数据不合规定")
            continue
        if temp == [404]:
            logging.error("404数据，不符合规范")
            continue
        if not temp:
            logging.info("数据已爬取完成")
            break
        # 添加本页数据
        allData.extend(temp)
        pi += 1
        with open(fileName, mode='w', encoding="utf-8") as  file:
            file.write("\n".join(map(str, allData)))


def recommendFund():
    """
        月收益<3月收益
        3月收益<6月收益
        6月收益<1年收益
        且本周+以上全红
        视为稳定的基金
        按照1年收益进行排序
        然后把top10制图发送邮件给自己
        脚本每月16号跑一次
    """
    columns = ['基金代码', '基金简称', '字符代码', '日期',
               '单位净值', '累计净值', '日增长率', '近1周',
               '近1月', '近3月', '近6月', '近1年',
               '近2年', '近3年', '今年来',
               '成立来']
    df = pd.DataFrame([i.strip().split(",")[:16] for i in allData], columns=columns)
    df = df.set_index("基金代码")
    # 去除空值
    df.dropna()
    # 将空白值替换为空值
    df.replace(to_replace=r'^\s*$', value=np.nan, regex=True, inplace=True)
    # 清洗数据(去除垃圾数据)
    df.query("单位净值==单位净值", inplace=True)
    df.query("近1周==近1周", inplace=True)
    df.query("近1月==近1月", inplace=True)
    # 填充数据（因为某些新生基金近1年、近2年为空，所以用其他列去填充）
    df['近3月'].fillna(df['近1月'], inplace=True)
    df['近6月'].fillna(df['近3月'], inplace=True)
    df['近1年'].fillna(df['近6月'], inplace=True)
    df['近2年'].fillna(df['近1月'], inplace=True)
    print(df.shape[0])
    # 更改类型
    df["近1周"] = df["近1周"].astype("float")
    df["近1月"] = df["近1月"].astype("float")
    df["近3月"] = df["近3月"].astype("float")
    df["近6月"] = df["近6月"].astype("float")
    df["近1年"] = df["近1年"].astype("float")
    df["近2年"] = df["近2年"].astype("float")
    # 去除负数据
    df.query("近1月>0", inplace=True)
    print(df.shape[0])
    df.query("近3月>0", inplace=True)
    print(df.shape[0])
    df.query("近6月>0", inplace=True)
    print(df.shape[0])
    df.query("近1年>0", inplace=True)
    print(df.shape[0])
    df.query("近2年>0", inplace=True)
    # 稳定基金查询
    df.query("近3月>=近1月 and 近6月>=近3月 and 近1年>=近6月 and 近2年>=近1年", inplace=True)
    print(df.shape[0])
    df = df.sort_values(by="近1年", ascending=False)[:20]
    fig, ax = plt.subplots(figsize=(35, 40))
    df[['近1月', '近3月', '近6月', '近1年',
        '近2年']].plot.bar(subplots=True, ax=ax, rot=0)
    fig.savefig(f"{fileName}推荐.png", quality=10)


if __name__ == '__main__':

    if os.path.exists(fileName):
        logging.info("导入本地数据")
        with open(fileName, mode='r', encoding="utf-8") as  file:
            allData = file.readlines()
    else:
        logging.info("开始爬取数据")
        getFundData()
        logging.info("数据爬取已结束")
    recommendFund()
