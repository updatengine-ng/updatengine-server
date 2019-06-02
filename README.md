# UpdatEngine-server

Version 3.0.1

UpdatEngine Server is a web app allowing people to inventory computer an server, deploy software and create profile to apply on inventoried machines for Windows and Linux.

- [History](#history)
- [Project features](#project-features)
- [New features and versions changes](#new-features-and-versions-changes)
- [Install](#install)
- [Upgrade from 2.1.1/Django 1.6.2](#upgrade-from-211django-162)
- [Update](#update)
- [Links](#links)
- [License](#license)

## History
UpdatEngine client and server was originally written by Yves Guimard.
He had to stop his participation in the project in July 2017.
Since version 2.1.1 of 2014, there was not much evolution for the server part and this repository has no other pretensions than to try to improve the functionalities.
Thanks to Yves, to the developers who participated and still participates as well as to the users.

## Project features
- Python 2.7 / Django 1.11 LTS project
- Tested with Debian 8, Ubuntu 16.04, Ubuntu 18.04, CentOs 7

## New features and versions changes
### v3.0
- Interface:
  - The chosen language remains displayed
  - Fix some translations in 'Export as CSV' and 'Mass update'
  - An update information is displayed in the menu below the current version number when a new version is available
- Deployment conditions:
  - New conditions:
    - Compatible with all UpdatEngine-client versions:
      - 'Host name is', 'Host name is not': Single value or comma separated list of values
      - 'IP address is', 'IP address is not': IP or network address / Single value or a comma separated list of values
    - Extended conditions only compatible with client versions from 3.0:
      - 'File exists', 'File doesn't exists'
      - 'Directory exists', 'Directory doesn't exists'
      - 'File or directory exists', 'File or directory doesn't exists'
      - 'SHA-256 hash is', 'SHA-256 hash is not': if file doesn't exist then client returns 'undefined' value
      - 'Command exit code is', 'Command exit code is not': if command doesn't exist then client returns 'undefined' value. Execution timed out after 30 seconds.
  - Allow the mutliple use of wildcard '*' in conditions 'software' and 'hostname' 
  - Allow the use of characters '&', '<' and '>' in the packages name, description and command

## Install
See [**2.1.1 installation documentation**](https://updatengine.com/) for details

Quickly (for debian/ubuntu):
  ```
sudo apt-get install apache2 libapache2-mod-wsgi python2.7 python-virtualenv python-pip libxml2-dev libxslt-dev python-dev libmysqlclient-dev git-core mysql-server
sudo virtualenv --distribute --no-site-packages -p /usr/bin/python2.7 /var/www/UE-environment
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

sudo /var/www/UE-environment/bin/pip install --upgrade distribute
sudo /var/www/UE-environment/bin/pip install --upgrade setuptools
sudo /var/www/UE-environment/bin/pip install -r /var/www/UE-environment/updatengine-server/requirements/pip-packages.txt

mysqladmin -u root -p create updatengine
mysql -u root -p -e "GRANT ALL PRIVILEGES ON updatengine.* TO 'updatengineuser'@'localhost' IDENTIFIED by 'unmotdepasse' WITH GRANT OPTION;"
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql
# You may see some warnings such as below, but don't worry about this. This files are used by 'tzselect' linux command and are not timezone.
# Warning: Unable to load '/usr/share/zoneinfo/iso3166.tab' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/leap-seconds.list' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/zone.tab' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/zone1970.tab' as time zone. Skipping it.
sudo service mysql restart

sudo cp /var/www/UE-environment/updatengine-server/updatengine/settings.py.model /var/www/UE-environment/updatengine-server/updatengine/settings.py
# and now modify settings.py

sudo cp /var/www/UE-environment/updatengine-server/requirements/apache-updatengine.conf /etc/apache2/sites-available/apache-updatengine.conf
sudo a2ensite apache-updatengine
sudo a2enmod wsgi
sudo service apache2 restart

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/configuration_initial_data.yaml
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/groups_initial_data.yaml

sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/static/
sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/media/

sudo service apache2 restart

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py createsuperuser
  ```

## Upgrade from 2.1.1/Django 1.6.2
Since UE Server now uses Django 1.11.13 and its integrate migration tools with new initial migration files, here is a clean solution to upgrade and keep your database.
After this upgrade, next 'migrations' will be easier than the procedure below.

Quickly (for debian/ubuntu):
  ```
# Backup existing database (for security reason)
# To restore : 'mysqladmin -u root -p drop updatengine' then
# recreate empty db and 'gunzip < ~/updatengine.sql.gz | mysql -u root -p updatengine'
mysqldump -u root -p updatengine | gzip -9 > ~/updatengine.sql.gz

# Move existing UE site (backup old version)
sudo mv /var/www/UE-environment/ /var/www/UE-environment_1.6.2/

# Install new version
sudo virtualenv --distribute --no-site-packages -p /usr/bin/python2.7 /var/www/UE-environment
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

sudo /var/www/UE-environment/bin/pip install --upgrade pip distribute setuptools
sudo /var/www/UE-environment/bin/pip install -r /var/www/UE-environment/updatengine-server/requirements/pip-packages.txt

sudo cp /var/www/UE-environment/updatengine-server/updatengine/settings.py.model /var/www/UE-environment/updatengine-server/updatengine/settings.py
# and now MODIFY settings.py

# Adapt the database ( add new fields, fake migration, remove 'south' table)
/var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py dbshell

ALTER TABLE inventory_entity ADD ip_range VARCHAR(200);
CREATE TABLE `configuration_globalconfig` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `show_warning` varchar(3) NOT NULL, `remove_duplicate` varchar(3) NOT NULL);
DROP TABLE IF EXISTS `south_migrationhistory`;
DROP TABLE IF EXISTS `django_migrations`;
quit

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate --fake-initial

# Here, your global deployment period is reset to initial value
# so keep in mind that you must set your own values in configuration menu
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/configuration_initial_data.yaml
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/groups_initial_data.yaml

# Copy deployment packages
rsync -av /var/www/UE-environment_1.6.2/updatengine-server/updatengine/media/package-file/* /var/www/UE-environment/updatengine-server/updatengine/media/package-file/

sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/static/
sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/media/

sudo service apache2 restart

# If new site works perfectly then delete old UE site (DANGER impossible to go back):
# sudo rm -rf /var/www/UE-environment_1.6.2
  ```

## Update
To update an existing version do :
  ```
cd /var/www/UE-environment/updatengine-server/
sudo git checkout --track origin/master
sudo git pull
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate
# In case of 'Table already exist' error then run this before retry 'migrate' :
# sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate --fake deploy 0002_auto_20180605_1910
sudo service apache2 restart
  ```
  
## Links
- French Google discussion group : https://groups.google.com/forum/#!forum/updatengine-fr
- Old official site : https://updatengine.com/
- Site archive : https://web.archive.org/web/20170318143615/http://www.updatengine.com:80/

## License
GPL-2.0
