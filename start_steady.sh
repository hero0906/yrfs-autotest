#升级前要吧脚本kill了。

cd /caoyi/test/autotest
echo -e "run_business"
ps aux|grep "run_business"|grep -v grep |awk '{print $2}'|xargs -I {} kill -9 {}
python3 script/yrfs_update.py -t all 
python3 script/run_business.py &
