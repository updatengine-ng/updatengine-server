###############################################################################
# UpdatEngine - Software Packages Deployment and Administration tool          #
#                                                                             #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                         #
# Copyright (C) Noël Martinon - noel.martinon@gmail.com                       #
#                                                                             #
# This program is free software; you can redistribute it and/or               #
# modify it under the terms of the GNU General Public License                 #
# as published by the Free Software Foundation; either version 2              #
# of the License, or (at your option) any later version.                      #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program; if not, write to the Free Software Foundation,     #
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.         #
###############################################################################

from django.shortcuts import render
from lxml import etree
from inventory.models import machine, typemachine, software, net, osdistribution, entity
from deploy.models import package, packagehistory, packagecustomvar
from configuration.models import deployconfig, globalconfig
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape
from django.db.models import Count, Max
from netaddr import IPNetwork, IPAddress
import sys
import re
from django.template import engines

django_engine = engines['django']


def compare_versions(version1, version2):
    ''' Compare two version string '''
    from packaging import version
    if version1 is None:
        version1 = ''
    if version2 is None:
        version2 = ''
    if version1 == version2:
        return 0
    try:
        return -1 if version.parse(version1) < version.parse(version2) else 1
    except:
        ver = [version1, version2]
        ver.sort()
        return -1 if ver[0] == version1 else 1


def is_deploy_authorized(m, handling, p=None):
    '''Function that define if deploy is authorized or not'''
    # Loading configuration datas
    config = deployconfig.objects.get(pk=1)
    now = datetime.now().time()
    deploy_auth = False
    # if a package time period is defined
    if p is not None:
        periods = p.timeprofiles.filter()
        if not periods:
            deploy_auth = True
        else:
            for period in periods:
                start = period.start_time
                end = period.end_time
                if (start <= now and now <= end) or (end <= start and (start <= now or now <= end)):
                    deploy_auth = True
                    break
    # if a global time period is defined
    elif config.activate_time_deploy == 'yes':
        start = config.start_time
        end = config.end_time
        if (start <= now and now <= end) or (end <= start and (start <= now or now <= end)):
            deploy_auth = True
        else:
            handling.append('<Info>Not in deployment period (global configuration)</Info>')
    # if a time period is defined for this machine
    elif m.timeprofile is not None:
        start = m.timeprofile.start_time
        end = m.timeprofile.end_time
        if (start <= now and now <= end) or (end <= start and (start <= now or now <= end)):
            deploy_auth = True
        else:
            handling.append('<Info>Not in deployment period (timeprofile)</Info>')
    else:
        deploy_auth = True
    return deploy_auth


def status(xml):
    '''Function that handle status client request'''
    handling = list()
    handling.append('<Response>')
    # read status from sent xml
    try:
        root = etree.fromstring(xml)
        mid = root.find('Mid').text
        pid = root.find('Pid').text
        status = root.find('Status').text
    except:
        handling.append('<Error>Error etree or find in xml</Error>')
        handling.append('</Response>')
        return handling
    try:
        # Update packagehistory status:
        m = machine.objects.get(pk=mid)
        p = package.objects.get(pk=pid)
        cv = {}
        for customvar in packagecustomvar.objects.filter(package=p, apply_on_commands=True):
            cv[customvar.name] = customvar.value
        if p.use_global_variables == 'yes':
            cv['username'] = m.username.replace(' (not logged in)', '')
            cv['hostname'] = m.name
            cv['domain'] = m.domain
        if len(cv) > 0:
            template = django_engine.from_string(p.command)
            p.command = template.render(cv, request=None)
        # Remove last record if it history status is 'Programmed'
        obj = packagehistory.objects.filter(machine=m, package=p)
        if obj:
            obj = obj.latest('date')
            if obj.status == 'Programmed':
                obj.delete()
        # Add status history in 'in progress', 'completed' and 'ready' if they are 5 minutes apart
        if status in ['Install in progress', 'Operation completed', 'Ready to download and execute']:
            # Use previous record with same status if it is less than 5 minutes old
            today = datetime.now(timezone.utc)
            date_max = today - timedelta(minutes=5)
            obj = packagehistory.objects.filter(machine=m, package=p, command=p.command, status=status, date__gt=date_max)
            if not obj:
                obj = packagehistory.objects.create(machine=m, package=p, command=p.command, status=status)
            else:
                obj = obj.latest('date')
        # Warning conditions reuses old records to avoid filling the base unnecessarily
        elif status.startswith('Warning condition:'):
            obj, created = packagehistory.objects.get_or_create(machine=m, package=p, command=p.command, status=status)
        # Add other status like installation errors
        else:
            obj = packagehistory.objects.create(machine=m, package=p, command=p.command, status=status)
        obj.name = p.name
        obj.description = p.description
        obj.command = p.command
        obj.packagesum = p.packagesum
        if p.packagesum != 'nofile':
            obj.filename = p.filename.path
        else:
            obj.filename = ''
        obj.status = status
        obj.save()
        # remove package from machine
        m.packages.remove(p)
        handling.append('Status saved')
    except:
        handling.append('Error when modifying status: %s' % str(sys.exc_info()))
    handling.append('</Response>')
    return handling


def get_extended_conditions(m, pack):
    '''This function get extended conditions of pack deployment package'''
    # Check custom package variables
    cv = {}
    for customvar in packagecustomvar.objects.filter(package=pack, apply_on_conditions=True):
        cv[customvar.name] = customvar.value
    if pack.use_global_variables == 'yes':
        cv['username'] = m.username.replace(' (not logged in)', '')
        cv['hostname'] = m.name
        cv['domain'] = m.domain

    handling = list()
    for condition in pack.conditions.filter(package=pack):
        if len(cv) > 0:
            template = django_engine.from_string(condition.softwarename)
            condition.softwarename = template.render(cv, request=None)
        if condition.depends == 'isfile':
            handling.append('<File>' + condition.softwarename + '</File>')
        elif condition.depends == 'notisfile':
            handling.append('<File>' + condition.softwarename + '</File>')
        elif condition.depends == 'isdir':
            handling.append('<Dir>' + condition.softwarename + '</Dir>')
        elif condition.depends == 'notisdir':
            handling.append('<Dir>' + condition.softwarename + '</Dir>')
        elif condition.depends == 'isfiledir':
            handling.append('<FileDir>' + condition.softwarename + '</FileDir>')
        elif condition.depends == 'notisfiledir':
            handling.append('<FileDir>' + condition.softwarename + '</FileDir>')
        elif condition.depends == 'hashis':
            handling.append('<Hash>' + condition.softwarename + '</Hash>')
        elif condition.depends == 'hashnot':
            handling.append('<Hash>' + condition.softwarename + '</Hash>')
        elif condition.depends == 'exitcodeis':
            handling.append('<ExitCode>' + encodeXMLText(condition.softwarename) + '</ExitCode>')
        elif condition.depends == 'exitcodenot':
            handling.append('<ExitCode>' + encodeXMLText(condition.softwarename) + '</ExitCode>')
    return handling


def check_conditions(m, pack, xml=None):
    '''This function check conditions of pack deployment package'''
    # Check custom package variables
    cv = {}
    for customvar in packagecustomvar.objects.filter(package=pack, apply_on_conditions=True):
        cv[customvar.name] = customvar.value
    if pack.use_global_variables == 'yes':
        cv['username'] = m.username.replace(' (not logged in)', '')
        cv['hostname'] = m.name
        cv['domain'] = m.domain

    # All types of conditions are checked one by one
    install = True

    # Check package deploy period
    if not is_deploy_authorized(m, None, pack):
        status('<Packagestatus>' +
               '<Mid>' + str(m.id) + '</Mid>' +
               '<Pid>' + str(pack.id) + '</Pid>' +
               '<Status>Warning condition: Package not in its deployment period</Status>' +
               '</Packagestatus>')
        return False

    # Check basic conditions
    if install is True:
        depends_filter = ['notinstalled', 'installed', 'is_W64_bits', 'is_W32_bits', 'system_is', 'system_not',
                          'language_is', 'lower', 'higher', 'hostname_in', 'hostname_not', 'username_in',
                          'username_not', 'ipaddr_in', 'ipaddr_not', 'vendor_in', 'vendor_not', 'product_in',
                          'product_not', 'type_in', 'type_not', 'executetimes', 'installtimes', 'executedelay',
                          'installdelay']
        for condition in pack.conditions.filter(package=pack, depends__in=depends_filter):
            if len(cv) > 0:
                template = django_engine.from_string(condition.softwarename)
                condition.softwarename = template.render(cv, request=None)
                template = django_engine.from_string(condition.softwareversion)
                condition.softwareversion = template.render(cv, request=None)

            # Software not installed (wildcards can be used for condition name)
            if condition.depends == 'notinstalled':
                nameregex = '^' + re.escape(condition.softwarename).replace('\\*', '.*') + '$'
                # Empty softwareversion is allowed (else django filter error!)
                if condition.softwareversion is None:
                    condition.softwareversion = ''
                # Check name exists
                if software.objects.filter(host_id=m.id, name__iregex=nameregex,
                                           version=condition.softwareversion).exists():
                    install = False

            # Software installed (wildcards can be used for condition name)
            elif condition.depends == 'installed':
                nameregex = '^' + re.escape(condition.softwarename).replace('\\*', '.*') + '$'
                # Empty softwareversion is allowed (else django filter error!)
                if condition.softwareversion is None:
                    condition.softwareversion = ''
                # Check name exists
                if not software.objects.filter(host_id=m.id, name__iregex=nameregex,
                                               version=condition.softwareversion).exists():
                    install = False

            # OS architecture is Windows 64bits
            elif condition.depends == 'is_W64_bits':
                if not osdistribution.objects.filter(host_id=m.id, name__icontains='Windows',
                                                     arch__contains='64').exists():
                    install = False

            # OS architecture is Windows 32bits
            elif condition.depends == 'is_W32_bits':
                if not osdistribution.objects.filter(host_id=m.id, name__icontains='Windows',
                                                     arch__contains='32').exists() and not osdistribution.objects.filter(
                    host_id=m.id, name__icontains='Windows', arch__contains='undefined').exists():
                    install = False

            # System name is (wildcards can be used)
            elif condition.depends == 'system_is':
                nameregex = re.escape(condition.softwarename).replace('\\*', '.*')
                # Empty softwareversion is allowed to check an empty version
                if condition.softwareversion is None:
                    condition.softwareversion = ''
                # Check name + version
                if condition.softwareversion != 'undefined':
                    if not osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex,
                                                         version__icontains=condition.softwareversion).exists():
                        install = False
                # Check name
                else:
                    if not osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                        install = False

            # System name is not (wildcards can be used)
            elif condition.depends == 'system_not':
                nameregex = re.escape(condition.softwarename).replace('\\*', '.*')
                # Empty softwareversion is allowed to check an empty version
                if condition.softwareversion is None:
                    condition.softwareversion = ''
                # Check name + version
                if condition.softwareversion != 'undefined':
                    if osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex,
                                                     version__icontains=condition.softwareversion).exists():
                        install = False
                # Check name
                else:
                    if osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                        install = False

            # Default system language is (ex: fr_FR)
            elif condition.depends == 'language_is':
                if m.language.upper() != condition.softwarename.upper():
                    install = False

            # Software not installed or version lower than (wildcards can be used for condition name)
            elif condition.depends == 'lower':
                nameregex = '^' + re.escape(condition.softwarename).replace('\\*', '.*') + '$'
                # Check if name exists
                if software.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                    # Empty softwareversion is useful to ignore the version and only check not installed
                    if condition.softwareversion is None:
                        install = False
                    else:
                        # Check if at least one of the versions is greater than condition
                        softtab = software.objects.filter(host_id=m.id, name__iregex=nameregex)
                        for s in softtab:
                            if compare_versions(s.version, condition.softwareversion) >= 0:
                                install = False
                                break

            # Software installed and version higher than (wildcards can be used for condition name)
            elif condition.depends == 'higher':
                nameregex = '^' + re.escape(condition.softwarename).replace('\\*', '.*') + '$'
                # Check if name exists
                if software.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                    # Empty softwareversion is useful to ignore the version and only check installed
                    if condition.softwareversion is not None:
                        # Check if all of the versions are lower than condition
                        softtab = software.objects.filter(host_id=m.id, name__iregex=nameregex)
                        for s in softtab:
                            if compare_versions(s.version, condition.softwareversion) <= 0:
                                install = False
                            else:
                                install = True
                                break
                else:
                    install = False
                    pass

            # Hostname is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'hostname_in':
                try:
                    # Check the list
                    hosts = condition.softwarename.split(',')
                    for hostname in hosts:
                        if not hostname:
                            continue
                        nameregex = '^' + re.escape(hostname).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.name, re.IGNORECASE):
                            install = True
                            break
                        else:
                            install = False
                except:
                    install = False
                    pass

            # Hostname is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'hostname_not':
                try:
                    # Check the list
                    hosts = condition.softwarename.split(',')
                    for hostname in hosts:
                        if not hostname:
                            continue
                        nameregex = '^' + re.escape(hostname).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.name, re.IGNORECASE):
                            install = False
                            break
                except:
                    install = False
                    pass

            # Username is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'username_in':
                try:
                    # Check the list
                    users = condition.softwarename.split(',')
                    for username in users:
                        if not username:
                            continue
                        nameregex = '^' + re.escape(username).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.username, re.IGNORECASE):
                            install = True
                            break
                        else:
                            install = False
                except:
                    install = False
                    pass

            # Username is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'username_not':
                try:
                    # Check the list
                    users = condition.softwarename.split(',')
                    for username in users:
                        if not username:
                            continue
                        nameregex = '^' + re.escape(username).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.username, re.IGNORECASE):
                            install = False
                            break
                except:
                    install = False
                    pass

            # IP address is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'ipaddr_in':
                try:
                    host_ip = net.objects.filter(host_id=m.id).values_list('ip', flat=True)
                    for host_ip_addr in host_ip:
                        host_ip_addr = ''.join(host_ip_addr)
                        networks = condition.softwarename.split(',')
                        for network in networks:
                            if not network:
                                continue
                            if IPAddress(host_ip_addr) in IPNetwork(network):
                                install = True
                                break
                            else:
                                install = False
                        if install is True:
                            break
                except:
                    install = False
                    pass

            # IP address is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'ipaddr_not':
                try:
                    host_ip = net.objects.filter(host_id=m.id).values_list('ip', flat=True)
                    for host_ip_addr in host_ip:
                        host_ip_addr = ''.join(host_ip_addr)
                        networks = condition.softwarename.split(',')
                        for network in networks:
                            if not network:
                                continue
                            if IPAddress(host_ip_addr) in IPNetwork(network):
                                install = False
                                break
                        if install is False:
                            break
                except:
                    install = False
                    pass

            # Vendor is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'vendor_in':
                try:
                    # Check the list
                    vendors = condition.softwarename.split(',')
                    for vendor in vendors:
                        if not vendor:
                            continue
                        nameregex = '^' + re.escape(vendor).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.vendor, re.IGNORECASE):
                            install = True
                            break
                        else:
                            install = False
                except:
                    install = False
                    pass

            # Vendor is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'vendor_not':
                try:
                    # Check the list
                    vendors = condition.softwarename.split(',')
                    for vendor in vendors:
                        if not vendor:
                            continue
                        nameregex = '^' + re.escape(vendor).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.vendor, re.IGNORECASE):
                            install = False
                            break
                except:
                    install = False
                    pass

            # Product is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'product_in':
                try:
                    # Check the list
                    products = condition.softwarename.split(',')
                    for product in products:
                        if not product:
                            continue
                        nameregex = '^' + re.escape(product).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.product, re.IGNORECASE):
                            install = True
                            break
                        else:
                            install = False
                except:
                    install = False
                    pass

            # Product is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'product_not':
                try:
                    # Check the list
                    products = condition.softwarename.split(',')
                    for product in products:
                        if not product:
                            continue
                        nameregex = '^' + re.escape(product).replace('\\*', '.*') + '$'
                        if re.match(nameregex, m.product, re.IGNORECASE):
                            install = False
                            break
                except:
                    install = False
                    pass

            # Machine type is in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'type_in':
                try:
                    # Check the list
                    typemachines = condition.softwarename.split(',')
                    for typemachine in typemachines:
                        if not typemachine:
                            continue
                        nameregex = '^' + re.escape(typemachine).replace('\\*', '.*') + '$'
                        if re.match(nameregex, str(m.typemachine), re.IGNORECASE):
                            install = True
                            break
                        else:
                            install = False
                except:
                    install = False
                    pass

            # Machine type is NOT in the list (comma separated list, wildcards can be used for condition name)
            elif condition.depends == 'type_not':
                try:
                    # Check the list
                    typemachines = condition.softwarename.split(',')
                    for typemachine in typemachines:
                        if not typemachine:
                            continue
                        nameregex = '^' + re.escape(typemachine).replace('\\*', '.*') + '$'
                        if re.match(nameregex, str(m.typemachine), re.IGNORECASE):
                            install = False
                            break
                except:
                    install = False
                    pass

            # Installation executed or completed a maximum of X times per day/week/month (calendar period, not duration)
            elif condition.depends == 'executetimes' or condition.depends == 'installtimes':
                try:
                    # For 'executetimes' we consider both 'Ready to download and execute' and
                    # 'Install in progress' as executions (tests create 'Install in progress').
                    if condition.depends == 'executetimes':
                        search_statuses = ['Ready to download and execute', 'Install in progress']
                    else:
                        search_statuses = ['Operation completed']
                    condition.softwarename = condition.softwarename.lower()
                    today = datetime.now(timezone.utc)
                    max_times_per_period = int(condition.softwareversion)
                    if condition.softwarename in ['day', 'jour']:
                        obj_in_period = packagehistory.objects.filter(machine_id=m.id, package_id=pack.id,
                                                                      status__in=search_statuses, date__year=today.year,
                                                                      date__month=today.month, date__day=today.day)
                    elif condition.softwarename in ['week', 'semaine']:
                        monday = today - timedelta(days=today.weekday())
                        sunday = today + timedelta(days=6 - today.weekday())
                        obj_in_period = packagehistory.objects.filter(machine_id=m.id, package_id=pack.id,
                                                                      status__in=search_statuses,
                                                                      date__range=(monday, sunday))
                    elif condition.softwarename in ['month', 'mois']:
                        obj_in_period = packagehistory.objects.filter(machine_id=m.id, package_id=pack.id,
                                                                      status__in=search_statuses, date__year=today.year,
                                                                      date__month=today.month)
                    else:
                        install = False

                    if install is True:
                        if len(obj_in_period) >= max_times_per_period:
                            install = False
                except:
                    install = False
                    pass

            # Installation executed or completed ta minimum interval of X minutes/hours/days (duration)
            elif condition.depends == 'executedelay' or condition.depends == 'installdelay':
                try:
                    search_status = 'Ready to download and execute' if condition.depends == 'executedelay' else 'Operation completed'
                    condition.softwarename = condition.softwarename.lower()
                    today = datetime.now(timezone.utc)
                    interval = int(condition.softwareversion)
                    if condition.softwarename in ['minutes']:
                        date_max = today - timedelta(minutes=interval)
                    elif condition.softwarename in ['hours', 'heures']:
                        date_max = today - timedelta(hours=interval)
                    elif condition.softwarename in ['days', 'jours']:
                        date_max = today - timedelta(days=interval)
                    else:
                        install = False

                    if install is True:
                        obj_in_period = packagehistory.objects.filter(machine_id=m.id, package_id=pack.id,
                                                                      status=search_status, date__gt=date_max)
                        if len(obj_in_period) > 0:
                            install = False
                except:
                    install = False
                    pass

            if install is False:
                break

    # Basic check to avoid asking client for unnecessary extended conditions
    if xml == b'BASIC_CHECK':
        return install;

    # Check extended conditions
    if install is True:
        try:
            root = etree.fromstring(xml)
        except:
            pass

        depends_filter = ['isfile', 'notisfile', 'isdir', 'notisdir', 'isfiledir', 'notisfiledir', 'hashis', 'hashnot',
                          'exitcodeis', 'exitcodenot']
        for condition in pack.conditions.filter(package=pack, depends__in=depends_filter):
            if len(cv) > 0:
                template = django_engine.from_string(condition.softwarename)
                condition.softwarename = template.render(cv, request=None)
                template = django_engine.from_string(condition.softwareversion)
                condition.softwareversion = template.render(cv, request=None)

            # File exists
            if condition.depends == 'isfile':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('File'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'False':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # File NOT exists
            elif condition.depends == 'notisfile':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('File'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'True':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Directory exists
            elif condition.depends == 'isdir':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('Dir'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'False':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Directory NOT exists
            elif condition.depends == 'notisdir':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('Dir'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'True':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Directory or File exists
            elif condition.depends == 'isfiledir':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('FileDir'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'False':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Directory or File NOT exists
            elif condition.depends == 'notisfiledir':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('FileDir'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == 'True':
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Hash file is (a non-existent file returns the value 'undefined')
            elif condition.depends == 'hashis':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('Hash'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus != condition.softwareversion:
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Hash file is NOT (a non-existent file returns the value 'undefined')
            elif condition.depends == 'hashnot':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('Hash'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == condition.softwareversion:
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Command exit code is
            elif condition.depends == 'exitcodeis':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('ExitCode'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus != condition.softwareversion:
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            # Command exit code is NOT
            elif condition.depends == 'exitcodenot':
                if xml is None:  # check in the loop to be able to get condition name in status
                    condition.name += ' (unsupported client)'
                    install = False
                else:
                    try:
                        for elem in root.findall('ExitCode'):
                            elname = elem.find('Name').text
                            elstatus = elem.find('Status').text
                            if elname == condition.softwarename:
                                if elstatus == condition.softwareversion:
                                    install = False
                                break
                    except:
                        condition.name += ' (malformed client response)'
                        install = False

            if install is False:
                break

    # Using try block because condition doesn't exist for package deployment period
    try:
        if condition.softwareversion is None:
            condition.softwareversion = ''
    except:
        pass

    if install is False:
        status('<Packagestatus>' +
               '<Mid>' + str(m.id) + '</Mid>' +
               '<Pid>' + str(pack.id) + '</Pid>' +
               '<Status>Warning condition: ' + escape(condition.name + '\nName: ' + condition.softwarename + '\nVersion: ' + condition.softwareversion) + '</Status>' +
               '</Packagestatus>')
    return install


def inventory(xml):
    '''This function handle client inventory request'''
    handling = list()
    handling.append('<Response>')
    try:
        root = etree.fromstring(xml)
        s = root.find('SerialNumber').text
        n = root.find('Hostname').text
        v = root.find('Manufacturer').text
        p = root.find('Product').text
        c = root.find('Chassistype').text

        try:
            u = root.find('Uuid').text
        except:
            u = 'Unknown'

        try:
            un = root.find('UserName').text
        except:
            un = 'Unknown'

        try:
            d = root.find('Domain').text
        except:
            d = 'Unknown'

        try:
            l = root.find('Language').text
        except:
            l = 'Unknown'

        try:
            clientversion = root.find('ClientVersion').text
        except:
            clientversion = 'Unknown'

        softsum = root.find('Softsum').text
        ossum = root.find('Ossum').text
        netsum = root.find('Netsum').text

    except:
        handling.append('<Error>Error etree or find in xml</Error>')
        handling.append('</Response>')
        return handling
    try:
        # Load default config
        config = deployconfig.objects.get(pk=1)

        # Typemachine import:
        ch, created = typemachine.objects.get_or_create(name=c)

        # Machine import
        if s is None:
            s = 'undefined'
        m, created = machine.objects.get_or_create(serial=s, name=n)
        m.vendor = v
        m.product = p
        m.uuid = u
        if un != 'Unknown' or m.username == 'Unknown':
            m.username = un
        if un == 'Unknown' and not ' (not logged in)' in m.username:
            m.username += ' (not logged in)'
        m.domain = d
        m.language = l
        m.typemachine_id = ch.id
        m.manualy_created = 'no'
        m.lastsave = datetime.now(timezone.utc)

        if created:
            m.entity = config.entity
            if config.entity is not None and config.entity.packageprofile is not None and config.packageprofile is None:
                m.packageprofile = config.entity.packageprofile
            else:
                m.packageprofile = config.packageprofile
            if config.entity is not None and config.entity.timeprofile is not None and config.timeprofile is None:
                m.timeprofile = config.entity.timeprofile
            else:
                m.timeprofile = config.timeprofile
        if not created:
            if m.entity is not None and m.entity.packageprofile is not None and m.entity.force_packageprofile == 'yes':
                m.packageprofile = m.entity.packageprofile

            if m.entity is not None and m.entity.timeprofile is not None and m.entity.force_timeprofile == 'yes':
                m.timeprofile = m.entity.timeprofile
        # System info import
        if ossum != m.ossum:
            m.ossum = ossum
            m.save()
            osdistribution.objects.filter(host_id=m.id, manualy_created='no').delete()
            for os in root.findall('Osdistribution'):
                osname = os.find('Name').text
                osversion = os.find('Version').text
                osarch = os.find('Arch').text
                ossystemdrive = os.find('Systemdrive').text
                try:
                    osdistribution.objects.create(name=osname, version=osversion, arch=osarch,
                                                  systemdrive=ossystemdrive, host_id=m.id, manualy_created='no')
                except:
                    handling.append('<Warning>Creation of System: ' + osname + ' -- ' + osversion + ' failed</Warning>')

        # Software import
        if softsum != m.softsum:
            # if software checksum has change:
            # delete all soft belonging to this machine and create new according to xml.
            m.softsum = softsum
            m.save()
            software.objects.filter(host_id=m.id, manualy_created='no').delete()
            slist = list()
            for soft in root.findall('Software'):
                try:
                    softname = soft.find('Name').text
                    if softname is None:
                        softname = 'Not defined'
                    softversion = soft.find('Version').text
                    softuninstall = soft.find('Uninstall').text
                    slist.append(software(name=softname, version=softversion, uninstall=softuninstall, host_id=m.id,
                                          manualy_created='no'))
                except:
                    pass
            try:
                software.objects.bulk_create(slist)
            except Exception as inst:
                handling.append('<Warning>Error saving software list: ' + str(inst) + '</Warning>')

        # Network import
        # Delete all network information belonging to this machine and create new according to xml.
        if netsum != m.netsum:
            m.netsum = netsum
            m.save()
            net.objects.filter(host_id=m.id, manualy_created='no').delete()
            for iface in root.findall('Network'):
                netip = iface.find('Ip').text
                netmask = iface.find('Mask').text
                netmac = iface.find('Mac').text
                try:
                    net.objects.create(ip=netip, mask=netmask, mac=netmac, host_id=m.id, manualy_created='no')
                except:
                    handling.append('<Warning>Creation of Network: ' + netip + ' -- ' + netmask + ' failed</Warning>')
        try:
            m.save()
            handling.append('<Import>Import ok</Import>')
        except:
            handling.append('<Error>can\'t save machine!</Error>')

        # Delete duplicated machines
        main_config = globalconfig.objects.get(pk=1)
        if main_config.remove_duplicate == 'yes':
            remove_duplicates()

        # Automatically set the entity
        if m.entity_id is not None:
            # get all ip addresses of the client
            host_ip = net.objects.filter(host_id=m.id).values_list('ip', flat=True)
            is_ip_matched = False  # Test to stop search after an ip matching an entity
            for host_ip_addr in host_ip:
                if is_ip_matched:
                    break
                host_ip_addr = ''.join(host_ip_addr)

                # get only entities with an ip_range value
                for entity_obj in entity.objects.exclude(ip_range__isnull=True).exclude(ip_range__exact=''):
                    network = entity_obj.ip_range.split(',')
                    # check client IP with all comma separated IP/CIDR networks (could be simple a IP Address)
                    for network_range in network:
                        try:
                            if not network_range:
                                continue
                            if IPAddress(host_ip_addr) in IPNetwork(network_range):
                                if m.entity_id != entity_obj.id:
                                    host_previous_entity = entity.objects.filter(id=m.entity_id)[0]
                                    handling.append('<Info>Entity updated for %s from \'%s\' to \'%s\'</Info>' % (
                                        m.name, host_previous_entity.name, entity_obj.name))
                                    m.entity_id = entity_obj.id
                                    m.entity.redistrib_url = entity_obj.redistrib_url
                                    m.save()
                                is_ip_matched = True
                                break
                        except:
                            handling.append('<Error>Invalid network in ip range for entity \'%s\' : \'%s\'</Error>' % (
                                entity_obj.name, network_range))
                            pass
                    if is_ip_matched:
                        break

        # packages program
        # check if it's the time to deploy and if it's authorized
        period_to_deploy = is_deploy_authorized(m, handling)
        config = deployconfig.objects.get(pk=1)
        # Use a set and not a list to automaticly remove duplicates
        package_to_deploy = set()
        if config.activate_deploy == 'yes':
            # Packages programmed manualy on machine
            for pack in m.packages.all().order_by('name'):
                package_to_deploy.add(pack)

            # Packages included in machine profilepackage
            if m.packageprofile:
                for pack in m.packageprofile.get_soft():
                    package_to_deploy.add(pack)
            else:
                handling.append('<Warning>No package profile set</Warning>')

            # Prepare list of extended conditions
            extended_conditions = list()
            if clientversion != 'Unknown':
                for pack in sorted(package_to_deploy, key=lambda package: package.name):
                    if (period_to_deploy or pack.ignoreperiod == 'yes'):
                        if check_conditions(m, pack, b'BASIC_CHECK'):
                            extended_conditions += get_extended_conditions(m, pack)
                if len(extended_conditions) > 0:
                    extended_conditions = list(set(extended_conditions))  # remove duplicates
                    extended_conditions.insert(0, '<Extended>')
                    extended_conditions.append('</Extended>')
                    handling += extended_conditions
            # Prepare response to Updatengine client
            if len(extended_conditions) == 0:
                for pack in sorted(package_to_deploy, key=lambda package: package.name):
                    if period_to_deploy or pack.ignoreperiod == 'yes':
                        cv = {}
                        for customvar in packagecustomvar.objects.filter(package=pack, apply_on_commands=True):
                            cv[customvar.name] = customvar.value
                        if pack.use_global_variables == 'yes':
                            cv['username'] = m.username.replace(' (not logged in)', '')
                            cv['hostname'] = m.name
                            cv['domain'] = m.domain
                        if len(cv) > 0:
                            template = django_engine.from_string(pack.command)
                            pack.command = template.render(cv, request=None)
                        if check_conditions(m, pack):
                            # Proceed 'install_timeout' option
                            option_timeout = '\ninstall_timeout_' + str(pack.install_timeout)
                            pack.command += option_timeout
                            # Proceed 'no_break_on_error' and 'download_no_restart' options
                            if pack.no_break_on_error == 'yes' or (
                                    pack.no_break_on_error == '-' and config.no_break_on_error == 'yes'):
                                if '\nno_break_on_error' not in pack.command:
                                    pack.command += '\nno_break_on_error'
                            if pack.download_no_restart == 'yes' or (
                                    pack.download_no_restart == '-' and config.download_no_restart == 'yes'):
                                if '\ndownload_no_restart' not in pack.command:
                                    pack.command += '\ndownload_no_restart'
                            # Check if updatengine-client supports 'no_break_on_error' option
                            if pack.command.find('no_break_on_error') != -1 and (
                                    clientversion == 'Unknown' or compare_versions(clientversion, '3.1') < 0):
                                status('<Packagestatus>' +
                                       '<Mid>' + str(m.id) + '</Mid>' +
                                       '<Pid>' + str(pack.id) + '</Pid>' +
                                       '<Status>Unsupported option for updatengine-client version \'' + clientversion + '\': Ignoring \'no_break_on_error\'</Status>' +
                                       '</Packagestatus>')
                                pack.command = re.sub('\r?\nno_break_on_error', '', pack.command)
                            if pack.packagesum != 'nofile':
                                if m.entity is not None and m.entity.redistrib_url:
                                    packurl = str(m.entity.redistrib_url) + str(pack.filename)
                                else:
                                    packurl = pack.filename.url
                            else:
                                packurl = ''
                            pack.name = encodeXMLText(pack.name)
                            pack.description = encodeXMLText(pack.description)
                            pack.command = encodeXMLText(pack.command)
                            handling.append('<Package>' +
                                            '<Id>' + str(m.id) + '</Id>' +
                                            '<Pid>' + str(pack.id) + '</Pid>' +
                                            '<Name>' + pack.name + '</Name>' +
                                            '<Description>' + pack.description + '</Description>' +
                                            '<Command>' + pack.command + '</Command>' +
                                            '<Packagesum>' + pack.packagesum + '</Packagesum>' +
                                            '<Packagehash>' + pack.packagehash + '</Packagehash>' +
                                            '<Url>' + packurl + '</Url>' +
                                            '</Package>')
        else:
            handling.append('<Info>Deployment function is not active</Info>')
    except:
        handling.append('Error when importing inventory: %s' % str(sys.exc_info()))
    handling.append('</Response>')
    return handling


def inventory_extended(xml):
    '''This function handle client extended inventory request'''
    handling = list()
    handling.append('<Response>')
    try:
        root = etree.fromstring(xml)
        s = root.find('SerialNumber').text
        n = root.find('Hostname').text
        try:
            clientversion = root.find('ClientVersion').text  # For UE-client>3.1
        except:
            clientversion = 'Unknown'

    except:
        handling.append('<Error>Error etree or find in xml</Error>')
        handling.append('</Response>')
        return handling
    try:
        if s is None:
            s = 'undefined'
        m = machine.objects.get(serial=s, name=n)
        handling.append('<Import>Import ok</Import>')

        # packages program
        # check if it's the time to deploy and if it's authorized
        period_to_deploy = is_deploy_authorized(m, handling)
        config = deployconfig.objects.get(pk=1)
        package_to_deploy = set()  # Use a set and not a list to automaticly remove duplicates
        if config.activate_deploy == 'yes':
            # Packages programmed manualy on machine
            for pack in m.packages.all().order_by('name'):
                package_to_deploy.add(pack)

            # Packages included in machine profilepackage
            if m.packageprofile:
                for pack in m.packageprofile.get_soft():
                    package_to_deploy.add(pack)

            # Prepare response to Updatengine client
            for pack in sorted(package_to_deploy, key=lambda package: package.name):
                if period_to_deploy or pack.ignoreperiod == 'yes':
                    if check_conditions(m, pack, xml):
                        cv = {}
                        for customvar in packagecustomvar.objects.filter(package=pack, apply_on_commands=True):
                            cv[customvar.name] = customvar.value
                        if pack.use_global_variables == 'yes':
                            cv['username'] = m.username.replace(' (not logged in)', '')
                            cv['hostname'] = m.name
                            cv['domain'] = m.domain
                        if len(cv) > 0:
                            template = django_engine.from_string(pack.command)
                            pack.command = template.render(cv, request=None)
                        # Proceed 'no_break_on_error' and 'download_no_restart' options
                        if pack.no_break_on_error == 'yes' or (pack.no_break_on_error == '' and config.no_break_on_error == 'yes'):
                            if '\nno_break_on_error' not in pack.command:
                                pack.command += '\nno_break_on_error'
                        if pack.download_no_restart == 'yes' or (pack.download_no_restart == '' and config.download_no_restart == 'yes'):
                            if '\ndownload_no_restart' not in pack.command:
                                pack.command += '\ndownload_no_restart'
                        # Check if updatengine-client supports 'no_break_on_error' option
                        if pack.command.find('no_break_on_error') != -1 and (
                                clientversion == 'Unknown' or compare_versions(clientversion, '3.1') < 0):
                            if clientversion == 'Unknown':
                                status('<Packagestatus>' +
                                       '<Mid>' + str(m.id) + '</Mid>' +
                                       '<Pid>' + str(pack.id) + '</Pid>' +
                                       '<Status>Possible use of unsupported option for updatengine-client version \'' + clientversion + '\': \'no_break_on_error\' need client version >= 3.1 but this warning is only removed after that version</Status>' +
                                       '</Packagestatus>')
                            else:
                                status('<Packagestatus>' +
                                       '<Mid>' + str(m.id) + '</Mid>' +
                                       '<Pid>' + str(pack.id) + '</Pid>' +
                                       '<Status>Unsupported option for updatengine-client version \'' + clientversion + '\': Ignoring \'no_break_on_error\'</Status>' +
                                       '</Packagestatus>')
                                pack.command = re.sub('\r?\nno_break_on_error', '', pack.command)
                        if pack.packagesum != 'nofile':
                            if m.entity is not None and m.entity.redistrib_url:
                                packurl = str(m.entity.redistrib_url) + str(pack.filename)
                            else:
                                packurl = pack.filename.url
                        else:
                            packurl = ''
                        pack.name = encodeXMLText(pack.name)
                        pack.description = encodeXMLText(pack.description)
                        pack.command = encodeXMLText(pack.command)
                        handling.append('<Package>' +
                                        '<Id>' + str(m.id) + '</Id>' +
                                        '<Pid>' + str(pack.id) + '</Pid>' +
                                        '<Name>' + pack.name + '</Name>' +
                                        '<Description>' + pack.description + '</Description>' +
                                        '<Command>' + pack.command + '</Command>' +
                                        '<Packagesum>' + pack.packagesum + '</Packagesum>' +
                                        '<Packagehash>' + pack.packagehash + '</Packagehash>' +
                                        '<Url>' + packurl + '</Url>' +
                                        '</Package>')
        else:
            handling.append('<Info>Deployment function is not active</Info>')
    except:
        handling.append('Error when importing extended inventory: %s' % str(sys.exc_info()))
    handling.append('</Response>')
    return handling


def public_soft_list(pack=None):
    handling = list()
    handling.append('<Response>')
    if pack is None:
        slist = package.objects.filter(public='yes')
    else:
        slist = package.objects.filter(id=pack, public='yes')

    for pack in slist:
        if pack.packagesum != 'nofile':
            packurl = pack.filename.url
        else:
            packurl = ''
        pack.name = encodeXMLText(pack.name)
        pack.description = encodeXMLText(pack.description)
        cv = {}
        for customvar in packagecustomvar.objects.filter(package=pack, apply_on_commands=True):
            cv[customvar.name] = customvar.value
        if pack.use_global_variables == 'yes':  # Ignored pack
            # cv['username'] = m.username.replace(' (not logged in)', '')
            # cv['hostname'] = m.name
            # cv['domain'] = m.domain
            continue
        if len(cv) > 0:
            template = django_engine.from_string(pack.command)
            pack.command = template.render(cv, request=None)
        pack.command = encodeXMLText(pack.command)
        handling.append('<Package>' +
                        '<Pid>' + str(pack.id) + '</Pid>' +
                        '<Name>' + pack.name + '</Name>' +
                        '<Description>' + pack.description + '</Description>' +
                        '<Command>' + pack.command + '</Command>' +
                        '<Packagesum>' + pack.packagesum + '</Packagesum>' +
                        '<Packagehash>' + pack.packagehash + '</Packagehash>' +
                        '<Url>' + packurl + '</Url>' +
                        '</Package>')
    handling.append('</Response>')
    return handling


def post(request):
    '''Post function redirect inventory and status client request
    to dedicated functions'''
    handling = list()

    if (request.POST.get('action')):
        action = request.POST.get('action')
        if (action == 'inventory') and (request.POST.get('xml')):
            xml = request.POST.get('xml')
            handling = inventory(xml)
            response = render(request, 'response_xml.html', {'list': handling}, content_type='application/xhtml+xml')
        elif (action == 'extended') and (request.POST.get('xml')):
            xml = request.POST.get('xml')
            handling = inventory_extended(xml)
            response = render(request, 'response_xml.html', {'list': handling}, content_type='application/xhtml+xml')
        elif action == 'status':
            xml = request.POST.get('xml')
            handling = status(xml)
            response = render(request, 'response_xml.html', {'list': handling})
        elif action == 'softlist':
            if request.POST.get('pack') is not None:
                handling = public_soft_list(request.POST.get('pack'))
            else:
                handling = public_soft_list()
            response = render(request, 'response_xml.html', {'list': handling})
        else:
            handling.append('<Error>No action found in sent xml</Error>')
            response = render(request, 'response_xml.html', {'list': handling})
    else:
        response = render(request, 'post_template.html')
    return response


def encodeXMLText(text):
    return text.replace('&', '&amp;').replace(">", "&gt;").replace("<", "&lt;")


def remove_duplicates():
    '''Remove all duplicated machines when an inventory is received (more recent entry is keeped)'''
    '''order_by is useful to set the more recent packageprofile if there are many duplicates for one machine'''
    duplicates = machine.objects.values('name').annotate(count=Count('id'), max_lastsave=Max('lastsave')).filter(
        count__gt=1)

    for duplicate in duplicates:
        current_host_obj = machine.objects.filter(name=duplicate['name'], lastsave=duplicate['max_lastsave'])[0]
        for host_obj in machine.objects.filter(name=duplicate['name']).exclude(lastsave=duplicate['max_lastsave']):
            # Set packageprofile to newest machine
            current_host_obj.packageprofile = host_obj.packageprofile
            current_host_obj.timeprofile = host_obj.timeprofile
            current_host_obj.comment = host_obj.comment
            current_host_obj.save()
            # Delete all entries
            software.objects.filter(host_id=host_obj.id).delete()
            osdistribution.objects.filter(host_id=host_obj.id).delete()
            net.objects.filter(host_id=host_obj.id).delete()
            packagehistory.objects.filter(machine_id=host_obj.id).delete()
            machine.objects.filter(id=host_obj.id).delete()
