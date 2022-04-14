from datetime import datetime
from py.xml import html
import pytest

@pytest.mark.optionalhook
def pytest_html_results_table_header(cells):
    cells.insert(2, html.th('Description'))
    #cells.insert(1, html.th('Time', class_='sortable time', col='time'))
    cells.pop()

@pytest.mark.optionalhook
def pytest_html_results_table_row(report, cells):
    cells.insert(2, html.td(report.description))
    #cells.insert(1, html.td(datetime.utcnow(), class_='col-time'))
    cells.pop()

@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    '''
    添加日志decription描述信息
    :param item:
    :return:
    '''
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)

@pytest.mark.optionalhook
def pytest_html_results_table_html(report, data):
    '''
    执行失败才记录日志，成功则不记录
    :param report:
    :param data:
    :return:
    '''
    if report.passed:
        del data[:]
        data.append(html.div('No log output captured.', class_='empty log'))

@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    """
    解决report遇到中文字符报错问题。
    :param item:
    :param call:
    :return:
    """
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)
    report.nodeid = report.nodeid.encode("utf-8").decode("unicode_escape")