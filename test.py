


# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time
# pools = []
#
# def spider():
#     page = 2
#     time.sleep(page)
#     print(f"crawl task{page} finished")
#     return page
#
# pool =  ThreadPoolExecutor(max_workers=4)
# p1 = pool.submit(spider)
# p2 = pool.submit(spider)
# p3 = pool.submit(spider)
# pools.append(p1)
# pools.append(p2)
# pools.append(p3)
# for t in as_completed(pools):
#     print(t.result())
from common.cluster import get_Cluster_Hostip

res = get_Cluster_Hostip()
print(res)