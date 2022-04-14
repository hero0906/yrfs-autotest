#python3 script/yrfs_update_chaowei.py -t all
#python3 script/yrfs_update_chaowei.py -t all -r
python3 runner.py
python3 script/feishu.py
#rm -fr /var/www/html/report.html
#report="report-`date "+%m%d-%H%M"`.html"
#cp logs/report.html /var/www/html/$report
