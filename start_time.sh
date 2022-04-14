#kill vdbench and business
#ps aux|grep -E "run_business|vdbench"|grep -v grep |awk '{print $2}'|xargs -I {} kill -9 {}
logdir="/tmp/autotest-`date +"%m-%d_%H-%m"`.log"
while true;do
   d=`date +%-H`
   if [[ $d -eq 01 ]]||[[ $d -eq 13 ]];then
       #cd /home/caoyi/autotest
       python3 script/yrfs_update_chaowei.py -t all |tee -a $logdir
       python3 script/yrfs_update_chaowei.py -t all -r
       python3 runner.py|tee -a $logdir
       python3 script/feishu.py &
   fi
   echo -e "`date`|sleep 1200!!!!!"
   sleep 1200
done
#./start_steady.sh
#rm -fr /var/www/html/report.html
#report="report-`date "+%m%d-%H%M"`.html"
#cp logs/report.html /var/www/html/$report
