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

from django.shortcuts import render_to_response
from django.template import RequestContext
from lxml import etree
from inventory.models import machine, typemachine, software, net, osdistribution
from deploy.models import package, packagehistory
from configuration.models import deployconfig
from datetime import datetime
from django.utils.timezone import utc
from xml.sax.saxutils import escape
import sys

def compare_versions(version1, version2):
    from distutils.version import StrictVersion, LooseVersion
    if v1 == "" or v2 == "":
        return 0
    v1 = version1.encode('ascii', 'ignore')
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

    # Software not installed (one wildcard can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='notinstalled'):
            if '*' in condition.softwarename:
                nametab = condition.softwarename.split('*')
                if software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1], version=condition.softwareversion).exists():
                    install = False
                    status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
            else:
                if software.objects.filter(host_id=m.id, name=condition.softwarename, version=condition.softwareversion).exists():
                    install = False
                    status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning Software already installed. Condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # Software installed (one wildcard can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='installed'):
            if '*' in condition.softwarename:
                nametab = condition.softwarename.split('*')
                if not software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1], version=condition.softwareversion).exists():
                    install = False
                    status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
            else:
                if not software.objects.filter(host_id=m.id, name=condition.softwarename, version=condition.softwareversion).exists():
                    install = False
                    status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # OS architecture is Windows 64bits
    if install == True:
        for condition in pack.conditions.filter(depends='is_W64_bits'):
            if not osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='64').exists():
                install = False
                status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # OS architecture is Windows 32bits
    if install == True:
        for condition in pack.conditions.filter(depends='is_W32_bits'):
            if not (osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='32').exists() or osdistribution.objects.filter(host_id=m.id, name__icontains='Windows', arch__contains='undefined').exists()):
                install = False
                status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # System name is (one wildcard can be used)
    if install == True:
        for condition in pack.conditions.filter(depends='system_is'):
            if condition.softwareversion != 'undefined':
                if '*' in condition.softwarename:
                    nametab = condition.softwarename.split('*')
                    if not osdistribution.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1], version__icontains=condition.softwareversion).exists():
                        install = False
                        status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                else:
                    if not osdistribution.objects.filter(host_id=m.id, name__icontains=condition.softwarename, version__icontains=condition.softwareversion).exists():
                        install = False
                        status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
            else:
                if '*' in condition.softwarename:
                    nametab = condition.softwarename.split('*')
                    if not osdistribution.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1]).exists():
                        install = False
                        status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                else:
                    if not osdistribution.objects.filter(host_id=m.id, name__icontains=condition.softwarename).exists():
                        install = False
                        status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # Default system language is (ex: fr_FR)
    if install == True:
        for condition in pack.conditions.filter(depends='language_is'):
            if m.language != condition.softwarename:
                install = False
                status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')

    # Software not installed or version lower than (one wildcard can be used for condition name)
    if install == True:
        for condition in pack.conditions.filter(depends='lower'):
            if '*' in condition.softwarename:
                nametab = condition.softwarename.split('*')
                if software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1]).exists():
                    softtab = software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1])
                    for s in softtab:
                        if compare_versions(s.version, condition.softwareversion) >= 0:
                            install = False
                            status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                            break
            else:
                if software.objects.filter(host_id=m.id, name=condition.softwarename).exists():
                    softtab = software.objects.filter(host_id=m.id, name=condition.softwarename)
                    for s in softtab:
                        if compare_versions(s.version, condition.softwareversion) >= 0:
                            install = False
                            status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                            break

    # Software installed and version higher than
    if install == True:
        for condition in pack.conditions.filter(depends='higher'):
            if '*' in condition.softwarename:
                nametab = condition.softwarename.split('*')
                if software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1]).exists():
                    softtab = software.objects.filter(host_id=m.id, name__startswith=nametab[0],name__endswith=nametab[1])
                    for s in softtab:
                        if compare_versions(s.version, condition.softwareversion) <= 0:
                            install = False
                            status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                            break
                else:
                    install = False
                    status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
            else:
                if software.objects.filter(host_id=m.id, name=condition.softwarename).exists():
                    softtab = software.objects.filter(host_id=m.id, name=condition.softwarename)
                    for s in softtab:
                        if compare_versions(s.version, condition.softwareversion) <= 0:
                            install = False
                            status('<Packagestatus><Mid>'+str(m.id)+'</Mid><Pid>'+str(pack.id)+'</Pid><Status>Warning condition: '+escape(condition.name)+'</Status></Packagestatus>')
                            break
                else:
                    install = False
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
            response = render_to_response("response_xml.html", {"list": handling}, mimetype="application/xhtml+xml")
        elif action == 'status':
            xml = request.POST.get('xml')
            handling = status(xml)
            response = render_to_response("response_xml.html", {"list": handling})
        elif action == 'softlist':
            if request.POST.get('pack') is not None:
                handling = public_soft_list(request.POST.get('pack'))
            else:
                handling = public_soft_list()
            response = render_to_response("response_xml.html", {"list": handling})
        else:
            handling.append('<Error>No action found in sent xml</Error>')
            response = render_to_response("response_xml.html", {"list": handling})
    else:
        response = render_to_response("post_template.html", context_instance=RequestContext(request))
    return response
