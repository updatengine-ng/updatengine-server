#!/bin/bash

################################################
## UpdatEngine-server installation script
## 2022/03/26
################################################
#
#             /!\ WARNING /!\
#
# This script might replaced some existing files so
# save them before running :
#
# /etc/apache2/sites-available/apache-updatengine.conf
# ${INST_DIR}/updatengine-server/updatengine/settings.py
# ${SSL_DIR}/updatengine.crt
# ${SSL_DIR}/updatengine.key
#
################################################


## Must be root user to install
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root user"
    exit
fi


################################################
###  -- UE server installation settings --   ###
################################################

## Values required
export INST_DIR=/srv
export VENV_DIR=/srv/venv/ue
export SSL_DIR=/etc/apache2
export DB_NAME=updatengine
export DB_USER=updatengineuser
export DB_PASSWORD=updatenginepwd
export SRV_URL=https://ue-server.domain.tld:1979
export SRV_PORT=1979
export ALLOWED_HOSTS="'ue-server.domain.tld', 'IP_SERVER'" # This value must be delimited with double quotes

## Email settings (optional but recommended)
#export EMAIL_ADMIN="('admin', 'admin@domain.tld')," # This value must be delimited with double quotes
#export EMAIL_FROM_SERVER=updatengine@domain.tld
#export EMAIL_FROM SERVER_ERROR=updatengine-error@domain.tld

## SMTP server (optional)
#export EMAIL_HOST=smtp.domain.tld
#export EMAIL_PORT=465
#export EMAIL_HOST_USER=USERNAME@your_adress.tld
#export EMAIL_HOST_PASSWORD=PASSWORD
#export EMAIL_USE_TLS=False
#export EMAIL_USE_SSL=True


################################################
###      -- Installation process --          ###
################################################

## Install linux packages and python modules
apt install sudo git -y
apt install apache2 python3 python3-dev python3-venv python3-pip python3-distutils libapache2-mod-wsgi-py3 git mariadb-server libmariadb-dev build-essential libxml2-dev libxslt-dev -y

mkdir -p ${VENV_DIR}

python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

git clone https://github.com/updatengine-ng/updatengine-server ${INST_DIR}/updatengine-server
cd ${INST_DIR}/updatengine-server

pip install --upgrade pip setuptools
pip install -r ${INST_DIR}/updatengine-server/requirements/pip-packages.txt

## Create database
mysqladmin create updatengine
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost' IDENTIFIED by '${DB_PASSWORD}' WITH GRANT OPTION;"
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
service mysql restart

## Copy and modify settings.py
cp ${INST_DIR}/updatengine-server/updatengine/settings.py.model ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "/^PROJECT_URL/c\PROJECT_URL = '${SRV_URL}'" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|'##updatengine_server.domain.tld##'|${ALLOWED_HOSTS}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|##database_name##|${DB_NAME}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|##database_user_name##|${DB_USER}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|##database_user_password##|${DB_PASSWORD}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|Europe/Paris|$(cat /etc/timezone)|" ${INST_DIR}/updatengine-server/updatengine/settings.py
sed -i "s|^SECRET_KEY = .*|SECRET_KEY = '$(tr -dc 'a-z0-9!@#\$%\(\-_=+)' < /dev/urandom | head -c50)'|" ${INST_DIR}/updatengine-server/updatengine/settings.py
[[ ! -z ${EMAIL_ADMIN} ]] && sed -i "s|#('admin', 'admin@your_adress.tld'),|${EMAIL_ADMIN}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
[[ ! -z ${EMAIL_FROM_SERVER} ]] && sed -i "s|updatengine@your_adress.tld|${EMAIL_FROM_SERVER}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
[[ ! -z ${EMAIL_FROM_SERVER_ERROR} ]] && sed -i "s|updatengine_error@your_adress.tld|${EMAIL_FROM_SERVER_ERROR}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
[[ ! -z ${EMAIL_HOST} ]] && sed -i "s|^#EMAIL_BACKEND =|EMAIL_BACKEND =|" ${INST_DIR}/updatengine-server/updatengine/settings.py
# Variables delimited by single quotes
PARAMS=( EMAIL_HOST EMAIL_HOST_USER EMAIL_HOST_PASSWORD )
for i in "${PARAMS[@]}"; do
	eval VALUE=\$$i
	[[ ! -z ${VALUE} ]] && sed -i "s|^#\?${i} = .*|${i} = '${VALUE}'|" ${INST_DIR}/updatengine-server/updatengine/settings.py
done
# Variables NOT delimited by single quotes
PARAMS=( EMAIL_PORT EMAIL_USE_TLS EMAIL_USE_SSL )
for i in "${PARAMS[@]}"; do
	eval VALUE=\$$i
	[[ ! -z ${VALUE} ]] && sed -i "s|^#\?${i} = .*|${i} = ${VALUE}|" ${INST_DIR}/updatengine-server/updatengine/settings.py
done

## Generate SSL certificat
a2ensite apache-updatengine
a2enmod wsgi
openssl req --new -newkey rsa:2048 -days 365 -nodes -x509 -keyout ${SSL_DIR}/updatengine.key -out ${SSL_DIR}/updatengine.crt -subj "/C=FR/ST=Guadeloupe/L=Saint-Claude/O=UpdatEngine-NG/CN=updatengine-ng.com"
a2enmod ssl

## Set apache configuration
envsubst < ${INST_DIR}/updatengine-server/requirements/apache-updatengine.conf > /etc/apache2/sites-available/apache-updatengine.conf 

## Start apache daemon
systemctl restart apache2

## Init database
${VENV_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py migrate
${VENV_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py runscript db_convert_utf8
${VENV_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py loaddata ${INST_DIR}/updatengine-server/initial_data/configuration_initial_data.yaml
${VENV_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py loaddata ${INST_DIR}/updatengine-server/initial_data/groups_initial_data.yaml

## Set directory owner
chown -R www-data:www-data ${INST_DIR}/updatengine-server/updatengine/static/
chown -R www-data:www-data ${INST_DIR}/updatengine-server/updatengine/media/

## Reload apache
systemctl reload apache2

## Create admin account
echo "Create superuser :"
${VENV_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py createsuperuser

