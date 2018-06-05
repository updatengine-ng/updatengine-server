# UpdatEngine-server

Version 2.1.2 RC1

## History
UpdatEngine client and server was originally written by Yves Guimard.

Other developers participated in the project especially Damien GUILLEM who just posted the latest version of UpdatEngine-client.

I'm an UpdatEngine's user since many years and it works great !

## What's new ?
UpdatEngine-server was upgraded :
- Django 1.11 LTS
- Deprecated migration tool 'South' removed
- Display column 'Operating system' added and 'Comment' removed from inventory machines
- New menu "General configuration" with theses options :
  - Remove duplicated machines
  - Hide 'Warning' messages in deployment history
- Script 'clear_history' to add in schedule task
- 100% compatibility with [**UpdatEngine-client 2.4.9.4**](https://github.com/dam09fr/updatengine-client/releases)
- Not tested with Ubuntu 18.04

## Links
- French Google discussion group : https://groups.google.com/forum/#!forum/updatengine-fr
- Old official site : https://updatengine.com/
- Site archive : https://web.archive.org/web/20170318143615/http://www.updatengine.com:80/
- Github Damien GUILLEM : https://github.com/dam09fr/

## Install
See [**2.1.1 installation documentation**](https://updatengine.com/) for details

Quickly (for debian/ubuntu):
  ```
sudo apt-get install apache2 libapache2-mod-wsgi python-virtualenv python-pip libxml2-dev libxslt-dev python-dev libmysqlclient-dev git-core mysql-server
sudo virtualenv --distribute --no-site-packages /var/www/UE-environment
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

sudo /var/www/UE-environment/bin/pip install --upgrade distribute
sudo /var/www/UE-environment/bin/pip install --upgrade setuptools
sudo /var/www/UE-environment/bin/pip install -r /var/www/UE-environment/updatengine-server/requirements/pip-packages.txt

mysqladmin -u root -p create updatengine
mysql -u root -p -e "GRANT ALL PRIVILEGES ON updatengine.* TO 'updatengineuser'@'localhost' IDENTIFIED by 'unmotdepasse' WITH GRANT OPTION;"
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql
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

## Upgrade
Quickly (for debian/ubuntu):
  ```
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

# Backup your settings:
sudo mv /var/www/UE-environment/updatengine-server/updatengine/settings.py /var/www/UE-environment/updatengine-server/updatengine/settings.py.bak

sudo cp /var/www/UE-environment/updatengine-server/updatengine/settings.py.model /var/www/UE-environment/updatengine-server/updatengine/settings.py
# and now modify settings.py

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate

# Here, your global deployment period is reset to initial value
# so keep in mind that you must set your own values in configuration menu
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/configuration_initial_data.yaml
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/groups_initial_data.yaml

sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/static/
sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/media/

sudo service apache2 restart
  ```
  
You may have an error with migration so you should update your database like this :
  ```
/var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py dbshell

ALTER TABLE inventory_entity ADD ip_range VARCHAR(200);
CREATE TABLE `configuration_globalconfig` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `show_warning` varchar(3) NOT NULL, `remove_duplicate` varchar(3) NOT NULL);

  ```
  
## License
GPL-2.0
