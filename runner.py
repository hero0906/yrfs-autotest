#!/usr/bin/env python3
#coding=utf-8

import pytest
import os
from config.consts import CASE_TYPE,LOG_PATH


if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

args = []

base = ["-vs","--tb=long"]
#module = ["-k " + MODULE_NAME]
#junit报告生成
junit = ["--junitxml=logs/report.xml"]
allure = ["--alluredir=" + LOG_PATH + "/allure-results", "--clean-alluredir"]
#collect = "--collect-only"
#html报告生成
html = ["--html=logs/report.html", "--self-contained-html", "--capture=tee-sys"]
color = ["--color=yes", "--code-highlight=yes", "--full-trace"]
#args.append(junit)
args = base + html + allure
#args.append(collect)

#判断用例是不是是部分执行还是全部执行，全部执行不需要-m参数
if CASE_TYPE == "collect":
    collect = "--collect-only"
    args.append(collect)

elif CASE_TYPE != "allTest" and CASE_TYPE != "collect":
    # 指定用例类型
    case = "-m %s" % CASE_TYPE
    #调试部分用例case
    #case = "testcase_func/test_tiering_v66.py::Test_TieringFunc::test_del_nonempty_dir"
    #case = "testcase_func/test_qos_func.py::Test_twoClientQosFunc::test_twoclient_write_mixbs"
    #case = "testcase_smoke/test_subdir_unmount.py"
    #case = "testcase_smoke/test_dir_quota.py"
    #case = "testcase_func/test_quota_func.py::Test_QuotaFuncmove::test_fourqotadir_move_threequotadir"
    args.append(case)

#执行全部设置参数
pytest.main(args)
