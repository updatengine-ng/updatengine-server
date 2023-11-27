#!/bin/bash

################################################
## UpdatEngine-server installation script
## 2023/11/27
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

# By default, the installer uses UE git branch 'master'. User can define
# another branch by declaring it in environment variable.
[ -z ${GIT_BRANCH} ] && GIT_BRANCH=master

################################################
###  -- UE server installation settings --   ###
################################################

# Set or read custom settings
mkdir -p ./custom

if [ ! -f ./custom/.env ]; then
    echo "################"
    echo "WARNING: The installer will used default site settings. Edit the 'custom/.env' file with your own settings."
    echo "################"
    wget -O ./custom/.env https://raw.githubusercontent.com/updatengine-ng/updatengine-server/${GIT_BRANCH}/install/debian/.env.default > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "Error: Unable to download the default environment settings ." >&2
      exit 1
    fi
    while true; do
        read -p "Do you wish to continue with the default settings instead of edit now (y/n) ? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) echo "Please set your settings in 'custom/.env' file and re-run the installation script."; cd "${INITIAL_DIR}"; exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
else
    echo "################"
    echo "INFORMATION: The installer is using the settings from '.env' file."
    echo "################"
fi

export $(cat ./custom/.env) > /dev/null 2>&1

# Set SECRET_KEY to a random value if not defined
if [ -z ${SECRET_KEY} ] || [ ${SECRET_KEY} = '!mustbechanged!' ]; then
    echo "Generate a secret key"
    export SECRET_KEY=$(dd bs=48 count=1 if=/dev/urandom 2>/dev/null | base64)
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" ./custom/.env
fi


################################################
###      -- Installation process --          ###
################################################

## Install linux packages and python modules
apt update
apt install git apache2 python3 python3-dev python3-venv python3-pip python3-distutils libapache2-mod-wsgi-py3 git mariadb-server libmariadb-dev build-essential libxml2-dev libxslt-dev -y

# Create directories
if [ ! -d "${VENV_DIR}" ]; then
    mkdir -p ${VENV_DIR}
    python3 -m venv ${VENV_DIR}
fi

[ ! -d "${INST_DIR}" ] && mkdir -p ${INST_DIR}
cd ${INST_DIR}

# Download or update UE-Server files
if [ ! -d "${INST_DIR}/updatengine-server" ]; then
    git clone https://github.com/updatengine-ng/updatengine-server -b ${GIT_BRANCH}
else
    git pull
fi

# Activate python virtual environment and install packages
source ${VENV_DIR}/bin/activate
cd ${INST_DIR}/updatengine-server

pip install --upgrade pip
pip install -r ${INST_DIR}/updatengine-server/requirements/pip-packages.txt

# Create database if it not exists
mysql -e "use ${DB_NAME}" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Create database ${DB_NAME}"
    mysql -e "CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4;"
    mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
fi

# Create database user
mysql -u "${DB_USER}" -p"${DB_PASSWORD}" -h localhost -e "use ${DB_NAME}" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Create database user ${DB_USER}"
    mysql -e "GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost' IDENTIFIED by '${DB_PASSWORD}';"
    if [ $? -ne 0 ]; then
        mysql -e "CREATE USER '${DB_USER}'@'localhost' IDENTIFIED by '${DB_PASSWORD}';"
        mysql -e "GRANT ALL ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';"
    fi
fi

# Set apache configuration
if [ ! -f /etc/apache2/sites-available/apache-updatengine.conf ] ; then
    echo "Set apache configuration"
    envsubst < ${INST_DIR}/updatengine-server/requirements/apache-updatengine.conf > /etc/apache2/sites-available/apache-updatengine.conf
    a2ensite apache-updatengine
    a2enmod wsgi
fi

# Generate SSL certificat
if [ ! -f ${SSL_DIR}/updatengine.key ] || [ ! -f ${SSL_DIR}/updatengine.crt ] ; then
    echo "Create a self-signed SSL certificate"
    openssl req --new -newkey rsa:2048 -days 365 -nodes -x509 -keyout ${SSL_DIR}/updatengine.key -out ${SSL_DIR}/updatengine.crt -subj "/O=UpdatEngine-NG/CN=updatengine-ng.com" > /dev/null 2>&1
fi
a2enmod ssl

# Start apache daemon
systemctl restart apache2

# Create settings.py using environment settings
echo "Create settings.py"
envsubst < ${INST_DIR}/updatengine-server/updatengine/settings.py.in > ${INST_DIR}/updatengine-server/updatengine/settings.py

# If settings_local.py exists, add it
echo "Check if ./custom/settings_local.py exists, if so copy it"
if [ -f ./custom/settings_local.py ]; then
    cp ./custom/settings_local.py ./updatengine/settings_local.py
fi

# Collect static files
echo "Collect static files"
python manage.py collectstatic --clear --noinput --verbosity=0

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate --noinput

# Load initial data if needed
( echo 'select count(*) from configuration_globalconfig;' | python manage.py dbshell | grep -v 'count' | grep 0 ) > /dev/null 2>&1
if [ "$?" = "0" ]; then
    echo "Import initial data"
    python manage.py loaddata initial_data/configuration_initial_data.yaml
    python manage.py loaddata initial_data/groups_initial_data.yaml
fi

# Set directory owner
chown -R www-data:www-data ${INST_DIR}/updatengine-server/updatengine/static/
chown -R www-data:www-data ${INST_DIR}/updatengine-server/updatengine/media/

# Reload apache
systemctl reload apache2

# Create admin account if none
( echo 'select count(*) from auth_user;' | python manage.py dbshell | grep -v 'count' | grep 0 ) > /dev/null 2>&1
if [ "$?" = "0" ]; then
    echo "################"
    echo "# CREATE ADMIN ACCOUNT"
    echo "# You can skip this step using CTRL-C and run the following command later:"
    echo "# cd ${INST_DIR}/updatengine-server && source ${VENV_DIR}/bin/activate && python manage.py createsuperuser && deactivate"
    echo "################"
    python manage.py createsuperuser
fi
