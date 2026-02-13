######################
# UpdatEngine-server #
######################

## 7.1.5 (2026-02-13):

**🐛 Bug fix **

- Fix html escaping in customvars

## 7.1.4 (2026-02-05):

**✨ Improvements**

- Enforce usage of Apache modules and backup old Apache configuration

**🐛 Bug fix **

- Fix bug when using customvars on empty condition's software version


## 7.1.3 (2026-01-14):

**🐛 Bug fix **

- Fix installation due changes for timezone from MariaDB 10.5
- Update README and scripts to install git in the first place

## 7.1.2 (2026-01-12):

**🐛 Bug fix **

- Fix package's filename URL to satisfy client and admin request

## 7.1.1 (2026-01-05):

**🐛 Bug fix **

- Fix media URL for default entity without URL redirection - regression since 7.1.0

## 7.1.0 (2026-01-03):

**✨ Improvements**

- Security improvement: Use FileWrapper instead of Web server for GUI file download. On the administration IP port, only the authenticated users are allow to download package using the package file URL.

**🔧 Maintenance**

- Bump gunicorn>=22.0.0

**🐛 Bug fix **

- Update installation script for use latest release version instead of master branch

## 7.0.1 (2025-12-21):

**🐛 Bug fix **

- Fix http error 405 on logout

## 7.0.0 (2025-12-12):

**🔧 Maintenance**

- Bump Django from 4.2.16 to 5.2.9
- Bump django-auth-ldap from 4.8.0 to 5.2.0
- Bump django-extensions from 3.2.3 to 4.1
- Bump django-grappelli from 4.0.1 to 4.0.3
- Bump lxml from 5.3.0 to 6.0.2
- Bump mysqlclient from 2.2.4 to 2.2.7
- Bump packaging from 24.1 to 25.0
- Bump pytz from 2024.1 to 2025.2
- Bump PyYAML from 6.0.2 to 6.0.3

## 6.1.3 (2025-12-12):

**✨ Improvements**

- Add optional environment value 'PORT_ADMIN' to distinguish the admin IP port from the client port

## 6.1.2 (2025-10-20):

- Fix help text for 'Enable failure tolerance' feature

## 6.1.1 (2025-08-11):

- Fix ignorance of 'download_no_restart' and 'no_break_on_error' when using the extended conditions

## 6.1.0 (2024-09-13):

- Fix bug when displaying the password_change_done page
- Fix AuthBackend authentication accepting bad passwords

## 6.0.1 (2024-09-13):

- Fix debian installation script for Python 3.12 compatibility
- Fix escape sequence in inventory views

## 6.0.0 (2024-10-24):

- Upgrade to Django 4.2.16 LTS
- Increase upload size limit to 5G
- Add 'custom variables' column to deploy/package page
- Increase package directory name length and make sure it is unique
- Add 'duplicate' feature to packages and conditions
- Add 'download_no_restart', 'no_break_on_error' and 'timeout' options in admin interface
- Modify configuration pages display
- Add 'execute' and 'install' conditions with 'max times per period' and 'min interval of'
- Display time profiles on packages page
- Add time profiles option to the packages
- Fix version comparison function and package status
- Update debian installation script
- Add custom variables feature
- Add SHA-512 hash for packages checksum
- Increase length of field uninstall on software
- Add LDAP support
- Add powershell deployment script for Windows GPO
- Add docker installation script

## 5.0.1 (2022-09-28):

- Fix error 'has_add_permission' on users page

## 5.0.0 (2022-09-16):

- Upgrade to Django 3.2 LTS
- Upgrade adminactions module to 1.15 version
- Add debian upgrade script
- Reorder the inventory columns (hostname is the first one)
- Add conditions vendor,product,type
- Display package command on several lines
- Add direct link to conditions on the packages page
- Add direct link to packages on the conditions page
- Add direct link to machines and packages on the history page
- Apply bulleted list style to 'packages' and 'conditions' on the deployment page
- Apply bulleted list style to 'packages' on the packageprofile page
- Fix version check

## 4.1.0 (2022-03-25):

- Update last release version using json
- Add debian installation script and new apache config
- Complete entity ip range help text
- Sort machines names in history filter list
- Add os version in inventory view

## 4.0.3 (2020-09-27):

- Fix white page on mass update
- Remove web directory indexes from apache conf

## 4.0.2 (2020-04-01):

- Fix wol issue
- Add lines to fix potential pip3 mysqlclient issue
- Fix version check

## 4.0.1 (2020-03-09):

- Add script db tables conversion to utf-8 (all languages support)
- Fix bug on remove os name or arch through the web gui
- Add 'username' condition and 'not logged in' tag

## 4.0.0 (2020-02-19):

- Port code to Python 3.7
- Migrate to Django 2.2
- Use the latest python packages in line with the upgrade (django-grappelli, mysqlclient...)

## 3.0.2 (2019-11-25):

- Optimizes extended conditions with client: Pre-check conditions to avoid asking client for unnecessary extended conditions if already a condition on the software is not satisfied.

## 3.0.1 (2019-06-20):

- Fix bug in imports/exports deployments
- Fix inventory dispatch (clients < 3.0 was sending 'undefined' for UserName, Domain and Language)

## 3.0 (2019-06-19):

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
- Deployment commands:
  - Usage of 'section_end' is deprecated and clients >= 3.0 pass over it. For retro compatibility, this option remain allow.

