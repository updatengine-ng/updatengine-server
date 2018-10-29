###################################################################################
# UpdatEngine - Software Packages Deployment and Administration tool              #
#                                                                                 #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                             #
#                                                                                 #
# This program is free software; you can redistribute it and/or                   #
# modify it under the terms of the GNU General Public License                     #
# as published by the Free Software Foundation; either version 2                  #
# of the License, or (at your option) any later version.                          #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program; if not, write to the Free Software                     #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA. #
###################################################################################

from django.shortcuts import render
from lxml import etree
from inventory.models import machine, typemachine, software, net, osdistribution, entity
from deploy.models import package, packagehistory
from configuration.models import deployconfig, globalconfig
from datetime import datetime
from django.utils.timezone import utc
from xml.sax.saxutils import escape
from django.db.models import Count, Max
from netaddr import IPNetwork, IPAddress
import sys

def compare_versions(version1, version2):
    from distutils.version import StrictVersion, LooseVersion
    if version1 == "":
        v1 = "0"
    else:
        v1 = version1.encode('ascii', 'ignore')
    if version2 == "":
        v2 = "0"
    else:
        v2 = version2.encode('ascii', 'ignore')
    try:
        return cmp(StrictVersion(v1), StrictVersion(v2))
    except ValueError:
        # in case of abnormal version number, fall back to LooseVersion
        try:
            return cmp(LooseVersion(v1), LooseVersion(v2))
        except TypeError:
            # certain LooseVersion comparions raise due to unorderable types, fallback to string comparison
            return cmp([str(v) for v in LooseVersion(v1).version], [str(v) for v in LooseVersion(v2).version])

def is_deploy_authorized(m,handling):
    """Function that define if deploy is authorized or not"""
    # Loading configuration datas
    config = deployconfig.objects.get(pk=1)
    now = datetime.now().time()
    deploy_auth = False
    # if a global time period is defined
    if config.activate_time_deploy == 'yes':
        start = config.start_time
        end = config.end_time
        if (start <= now and now <= end) or \
        (end <= start and (start <= now or now <= end)):
            deploy_auth = True
        else:
            deploy_auth = False
            handling.append('<info>Not in deployment period (global configuration)</info>')
        # if a time period is defined for this machine
    elif m.timeprofile is not None:
        start = m.timeprofile.start_time
        end = m.timeprofile.end_time
        if (start <= now and now <= end) or \
        (end <= start and (start <= now or now <= end)):
            deploy_auth = True
        else:
            deploy_auth = False
            handling.append('<info>Not in deployment period (timeprofile)</info>')
    else:
        deploy_auth = True
    return deploy_auth


def status(xml):
    """Function that handle status client request"""
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
        m = machine.objects.get(pk = mid)
        p = package.objects.get(pk = pid)
        obj, created = packagehistory.objects.get_or_create(machine=m,package=p,command=p.command,status=status)
        obj.name = p.name
        obj.description = p.description
        obj.command = p.command
        obj.packagesum = p.packagesum
        if p.packagesum != 'nofile':
            obj.filename = p.filename.path
        else:
            obj.filename = ''
        obj.status=status
        obj.save()
        # remove package from machine
        m.packages.remove(p)
        handling.append('Status saved')
    except:
        handling.append('Error when modifying status: %s' % str(sys.exc_info()))
    handling.append('</Response>')
    return handling

def check_conditions(m,pack):
    """This function check conditions of pack deployment package"""
    import re
    install = True
    # All types of conditions are checked one by one

    # Software not installed (wildcards can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='notinstalled'):
            nameregex = "^"+re.escape(condition.softwarename).replace('\*', '.*')+"$"
            # Empty softwareversion is allowed (else django filter error!)
            if condition.softwareversion == None:
                condition.softwareversion = ''
            # Check name exists
            if software.objects.filter(host_id=m.id, name__iregex=nameregex, version=condition.softwareversion).exists():
                install = False

    # Software installed (wildcards can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='installed'):
            nameregex = "^"+re.escape(condition.softwarename).replace('\*', '.*')+"$"
            # Empty softwareversion is allowed (else django filter error!)
            if condition.softwareversion == None:
                condition.softwareversion = ''
            # Check name exists
            if not software.objects.filter(host_id=m.id, name__iregex=nameregex, version=condition.softwareversion).exists():
                install = False

    # OS architecture is Windows 64bits
    if install == True:
        for condition in pack.conditions.filter(depends='is_W64_bits'):
            if not osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='64').exists():
                install = False

    # OS architecture is Windows 32bits
    if install == True:
        for condition in pack.conditions.filter(depends='is_W32_bits'):
            if not (osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='32').exists() or osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='undefined').exists()):
                install = False

    # System name is (wildcards can be used)
    if install == True:
        for condition in pack.conditions.filter(depends='system_is'):
            nameregex = re.escape(condition.softwarename).replace('\*', '.*')
            # Empty softwareversion is allowed to check an empty version
            if condition.softwareversion == None:
                condition.softwareversion = ''
            # Check name + version
            if condition.softwareversion != 'undefined':
                if not osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex, version__icontains=condition.softwareversion).exists():
                    install = False                
            # Check name
            else:
                if not osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                    install = False

    # System name is not (wildcards can be used)
    if install == True:
        for condition in pack.conditions.filter(depends='system_not'):
            nameregex = re.escape(condition.softwarename).replace('\*', '.*')
            # Empty softwareversion is allowed to check an empty version
            if condition.softwareversion == None:
                condition.softwareversion = ''
            # Check name + version
            if condition.softwareversion != 'undefined':
                if osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex, version__icontains=condition.softwareversion).exists():
                    install = False                
            # Check name
            else:
                if osdistribution.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                    install = False

    # Default system language is (ex: fr_FR)
    if install == True:
        for condition in pack.conditions.filter(depends='language_is'):
            if m.language.upper() != condition.softwarename.upper():
                install = False

    # Software not installed or version lower than (wildcards can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='lower'):
            nameregex = "^"+re.escape(condition.softwarename).replace('\*', '.*')+"$"
            # Check if name exists
            if software.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                # Empty softwareversion is useful to ignore the version
                if condition.softwareversion == None or condition.softwareversion == '':
                    return False
                # Check if at least one of the versions is greater than condition
                softtab = software.objects.filter(host_id=m.id, name__iregex=nameregex)
                for s in softtab:
                    if compare_versions(s.version, condition.softwareversion) >= 0:
                        install = False
                        break

    # Software installed and version higher than (wildcards can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='higher'):
            nameregex = "^"+re.escape(condition.softwarename).replace('\*', '.*')+"$"
            # Check if name exists
            if software.objects.filter(host_id=m.id, name__iregex=nameregex).exists():
                # Empty softwareversion is useful to ignore the version
                if condition.softwareversion == None or condition.softwareversion == '':
                    return True
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

    if install == False:
        status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    return install


def inventory(xml):
    """This function handle client inventory request"""
    handling = list()
    handling.append('<Response>')
    try:
        root = etree.fromstring(xml)
        s = root.find('SerialNumber').text
        n = root.find('Hostname').text
        v = root.find('Manufacturer').text
        p = root.find('Product').text
        c = root.find('Chassistype').text
        # Maintain compatibility with old (< 2.3) UpdatEngine Client
        try:
            u = root.find('Uuid').text
            un = root.find('UserName').text
            d = root.find('Domain').text
            l = root.find('Language').text
        except:
            u = 'Unknown'
            un = 'Unknown'
            d = 'Unknown'
            l = 'Unknown'
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
        if s == None:
            s = 'undefined'
        m, created = machine.objects.get_or_create(serial=s, name=n)
        m.vendor=v
        m.product=p
        m.uuid = u
        if un != 'Unknown' or m.username == 'Unknown':
            m.username = un
        m.domain = d
        m.language = l
        m.typemachine_id=ch.id
        m.manualy_created='no'
        m.lastsave = datetime.utcnow().replace(tzinfo=utc)

        if created:
	        m.entity = config.entity
	        if config.entity != None and config.entity.packageprofile != None and config.packageprofile == None:
			m.packageprofile = config.entity.packageprofile
		else:
	        	m.packageprofile = config.packageprofile
	        if config.entity != None and config.entity.timeprofile != None and config.timeprofile == None:
			m.timeprofile = config.entity.timeprofile
		else:
			m.timeprofile = config.timeprofile
        if not created:
		if m.entity != None and m.entity.packageprofile != None and m.entity.force_packageprofile == 'yes':
                        m.packageprofile = m.entity.packageprofile

		if m.entity != None and m.entity.timeprofile != None and m.entity.force_timeprofile == 'yes':
                        m.timeprofile = m.entity.timeprofile
        # System info import
        if ossum != m.ossum:
            m.ossum = ossum
            m.save()
            osdistribution.objects.filter(host_id=m.id,manualy_created='no').delete()
            for os in root.findall('Osdistribution'):
                    osname = os.find('Name').text
                    osversion = os.find('Version').text
                    osarch = os.find('Arch').text
                    ossystemdrive = os.find('Systemdrive').text
                    try:
                     osdistribution.objects.create(name = osname, version = osversion, arch = osarch, systemdrive = ossystemdrive, host_id=m.id, manualy_created='no')
                    except:
                        handling.append('<warning>creation off System: '+osname+' -- '+osversion+' failed</warning>')

        # Software import
        if softsum != m.softsum:
            # if software checksum has change:
            #delete all soft belonging to this machine and create new according to xml.
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
                    slist.append(software(name = softname, version = softversion,uninstall=softuninstall, host_id=m.id, manualy_created='no'))
                except:
                    pass
            try:
               software.objects.bulk_create(slist)
            except Exception as inst:
               handling.append('<warning>Error saving software list: '+str(inst)+'</warning>')

        # Network import
        # Delete all network information belonging to this machine and create new according to xml.
        if netsum != m.netsum:
            m.netsum = netsum
            m.save()
            net.objects.filter(host_id=m.id,manualy_created='no').delete()
            for iface in root.findall('Network'):
                netip = iface.find('Ip').text
                netmask = iface.find('Mask').text
                netmac = iface.find('Mac').text
                try:
                    net.objects.create(ip = netip, mask = netmask, mac = netmac, host_id = m.id, manualy_created='no')
                except:
                    handling.append('<warning>creation off Network: '+netip+' -- '+netmask+' failed</warning>')
        try:
            m.save()
            handling.append('<Import>Import ok</Import>')
        except:
            handling.append('<Error>can\'t save machine!</Import>')

        # Delete duplicated machines
        main_config = globalconfig.objects.get(pk=1)
        if main_config.remove_duplicate == 'yes':
            remove_duplicates()

        # Automatically set the entity
        #
        # IMPORTANT!
        # 'ip_range' field must exist in database. It can be added with this commands :
        #     /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py dbshell
        #     ALTER TABLE inventory_entity ADD ip_range VARCHAR(200);
        #
        if m.entity_id is not None:
            # get all ip addresses of the client
            host_ip = net.objects.filter(host_id=m.id).values_list('ip', flat=True)
            is_ip_matched = False # Test to stop search after an ip matching an entity
            for host_ip_addr in host_ip:
                if is_ip_matched:
                    break
                host_ip_addr = "".join(host_ip_addr)

                # get only entities with an ip_range value
                for entity_obj in entity.objects.exclude(ip_range__isnull=True).exclude(ip_range__exact=''):
                    network = entity_obj.ip_range.split(',')
                    # check client IP with all comma separated IP/CIDR networks (could be simple a IP Address)
                    for network_range in network:
                        try:
                            if IPAddress(host_ip_addr) in IPNetwork(network_range):
                               if m.entity_id != entity_obj.id:
                                   host_previous_entity = entity.objects.filter(id = m.entity_id)[0]
                                   handling.append("<info>Entity updated for %s from '%s' to '%s'</info>"% (m.name,host_previous_entity.name,entity_obj.name))
                                   m.entity_id = entity_obj.id
                                   m.entity.redistrib_url = entity_obj.redistrib_url
                                   m.save()
                               is_ip_matched = True
                               break
                        except:
                            handling.append("<error>Invalid network in ip range for entity '%s' : '%s'</error>"% (entity_obj.name,network_range))
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

             # Prepare response to Updatengine client
            for pack in sorted(package_to_deploy ,key=lambda package: package.name):
                if period_to_deploy or pack.ignoreperiod == 'yes':
                    if check_conditions(m, pack):
                        if pack.packagesum != 'nofile':
                            if m.entity != None and m.entity.redistrib_url:
                                packurl = str(m.entity.redistrib_url)+str(pack.filename)
                            else:
                                packurl = pack.filename.url
                        else:
                            packurl = ''
                        handling.append('<Package>\n\
                                <Id>'+str(m.id)+'</Id>\n\
                                <Pid>'+str(pack.id)+'</Pid>\n\
                                <Name>'+pack.name+'</Name>\n\
                                <Description>'+pack.description+'</Description>\n\
                                <Command>'+pack.command+'</Command>\n\
                                <Packagesum>'+pack.packagesum+'</Packagesum>\n\
                                <Url>'+packurl+'</Url>\n</Package>')
        else:
            handling.append('<info>deployment function is not active </info>')
    except:
        handling.append('Error when importing inventory: %s' % str(sys.exc_info()))
    handling.append('</Response>')
    return handling

def public_soft_list(pack=None):
    handling = list()
    handling.append('<Response>\n')
    if pack is None:
        slist = package.objects.filter(public='yes')
    else:
        slist = package.objects.filter(id=pack, public='yes')

    for pack in slist:
        if pack.packagesum != 'nofile':
            packurl = pack.filename.url
        else:
            packurl = ''
        handling.append('<Package>\n\
            <Pid>'+str(pack.id)+'</Pid>\n\
            <Name>'+pack.name+'</Name>\n\
            <Description>'+pack.description+'</Description>\n\
            <Command>'+pack.command+'</Command>\n\
            <Packagesum>'+pack.packagesum+'</Packagesum>\n\
            <Url>'+packurl+'</Url>\n</Package>')
    handling.append('</Response>')
    return handling

def post(request):
    """Post function redirect inventory and status client request
    to dedicated functions"""
    handling = list()

    if (request.POST.get('action')):
        action = request.POST.get('action')
        if (action == 'inventory') and (request.POST.get('xml')):
            xml = request.POST.get('xml')
            handling = inventory(xml)
            response = render(request, "response_xml.html", {"list": handling}, content_type="application/xhtml+xml")
        elif action == 'status':
            xml = request.POST.get('xml')
            handling = status(xml)
            response = render(request, "response_xml.html", {"list": handling})
        elif action == 'softlist':
            if request.POST.get('pack') is not None:
                handling = public_soft_list(request.POST.get('pack'))
            else:
                handling = public_soft_list()
            response = render(request, "response_xml.html", {"list": handling})
        else:
            handling.append('<Error>No action found in sent xml</Error>')
            response = render(request, "response_xml.html", {"list": handling})
    else:
        response = render(request, "post_template.html")
    return response

def remove_duplicates():
    '''Remove all duplicated machines when an inventory is received (more recent entry is keeped)'''
    '''order_by is useful to set the more recent packageprofile if there are many duplicates for one machine'''
    duplicates = machine.objects.values('name').annotate(count=Count('id'),max_lastsave=Max('lastsave')).filter(count__gt=1)

    for duplicate in duplicates:
        current_host_obj = machine.objects.filter(name = duplicate['name'], lastsave = duplicate['max_lastsave'])[0]
        for host_obj in machine.objects.filter(name = duplicate['name']).exclude(lastsave = duplicate['max_lastsave']):
            # Set packageprofile to newest machine
            current_host_obj.packageprofile = host_obj.packageprofile
            current_host_obj.timeprofile = host_obj.timeprofile
            current_host_obj.save()
            # Delete all entries
            software.objects.filter(host_id=host_obj.id).delete()
            osdistribution.objects.filter(host_id=host_obj.id).delete()
            net.objects.filter(host_id=host_obj.id).delete()
            packagehistory.objects.filter(machine_id=host_obj.id).delete()
            machine.objects.filter(id=host_obj.id).delete()
