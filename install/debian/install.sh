#!/bin/bash

################################################
## UpdatEngine-server installation script
## 2024/12/05
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

# Must be root user to install
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root user"
    exit 1
fi

# Must be in root user's environment
if [[ ":$PATH:" != *":/usr/sbin:"* ]]; then
    echo "The path is missing /usr/sbin, please ensure to use the command 'su -' to switch to the full root user's environment."
    exit 1
fi

# Check this current script line endings style
grep -l $'\r' "${BASH_SOURCE[0]}" && echo "Error: Please convert the file "${BASH_SOURCE[0]}" to Linux-style line endings (LF) then run it again. You can use the next command \"sed -i 's/\r//g' ${BASH_SOURCE[0]}\"" && exit 1

# By default, the installer uses UE git branch 'master'. User can define
# another branch by declaring it in environment variable.
[ -z ${GIT_BRANCH} ] && GIT_BRANCH=master
echo "Using git branch ${GIT_BRANCH}"

# Set SCRIPT_DIR, 'custom' directory must be there
INITIAL_DIR=$( pwd )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

################################################
###  -- UE server installation settings --   ###
################################################

# Set or read custom settings
mkdir -p ./custom
if [ ! -f ./custom/.env ]; then
    echo "################"
    echo "WARNING: The installer will used default site settings. Edit the 'custom/.env' file with your own settings."
    echo "################"
    wget -O ./custom/.env https://raw.githubusercontent.com/updatengine-ng/updatengine-server/${GIT_BRANCH}/install/debian/custom.dist/.env.default > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "Error: Unable to download the default environment settings ." >&2
      exit 1
    fi
    while true; do
        read -p "Do you wish to continue with the default settings instead of edit now (y/n) ? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) echo "Please set your settings in 'custom/.env' file and run again the installation script."; cd "${INITIAL_DIR}"; exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
else
    echo "################"
    echo "INFORMATION: The installer is using the settings from '.env' file."
    echo "################"
fi

# Check and convert the .env line endings style
grep -l $'\r' ./custom/.env && sed -i 's/\r//g' ./custom/.env && echo "Information: The file './custom/.env' was converted from Windows-style line endings (CRLF) to Linux-style line endings (LF)."

# Export all key/value pairs from the '.env' file to the shell environment
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

# Install linux packages and python modules
apt update
apt install git apache2 python3 python3-dev python3-venv python3-pip \
    gettext-base libapache2-mod-wsgi-py3 git mariadb-server \
    libmariadb-dev build-essential libxml2-dev libxslt-dev \
    libldap2-dev libsasl2-dev pkg-config -y

# Create python virtual environment
if [ ! -d "${VENV_DIR}" ]; then
    mkdir -p ${VENV_DIR}
    python3 -m venv ${VENV_DIR}
fi

# Create UpdatEngine server directory
[ ! -d "${INST_DIR}" ] && mkdir -p ${INST_DIR}
cd ${INST_DIR}

# Download or update UE-Server files
if [ ! -d "${INST_DIR}/updatengine-server" ]; then
    git clone https://github.com/updatengine-ng/updatengine-server -b ${GIT_BRANCH}
else
    cd updatengine-server
    git fetch --all
    git reset --hard
    git checkout ${GIT_BRANCH}
    git reset --hard origin/${GIT_BRANCH}
    git pull
fi

# Activate python virtual environment and install packages
source ${VENV_DIR}/bin/activate
cd ${INST_DIR}/updatengine-server

python -m ensurepip --upgrade
pip install --upgrade setuptools
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

# Add custom/settings_local.py if it exists
if [ -f "${SCRIPT_DIR}/custom/settings_local.py" ]; then
    echo "Copy settings_local.py to updatengine-server directory"
    cp "${SCRIPT_DIR}/custom/settings_local.py" ./updatengine/settings_local.py
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

# Back to initial directory
cd "${INITIAL_DIR}"

# Deactivate the Python venv
deactivate
