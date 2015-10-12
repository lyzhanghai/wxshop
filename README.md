系统要求：
centos 6.x
mysql 5.1x
memcached

一 安装基本环境
1 安装系统环境
rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

yum -y install gcc nginx mysql-libs mysql-server mysql-devel memcached python-setuptools
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
/usr/bin/easy_install pip
yum install python-devel

2 安装pypy
yum -y install pypy-libs pypy pypy-devel

3 安装依赖
pip install PIL --allow-external PIL --allow-unverified PIL
pip install -r requirement.txt


二 项目配置
cd src
vi setting.py
#设置数据库和缓存服务器信息

#初始化数据库
python manager.py --cmd=syncdb

三 开始运行
python manager.py
