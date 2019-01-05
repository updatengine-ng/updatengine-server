from django.test import TestCase
from inventory.models import machine, software, osdistribution
from deploy.models import package, packagecondition
from inventory.views import *
class machineTestCase(TestCase):
    def setUp(self):
        # Define machine and software associated

        #machine Linux
        mlinux = machine.objects.create(serial='1234', name='mlinux', language = 'fr_CA')
        osdistribution.objects.create(name = 'Linux Mint', version = '15', arch = '64bits', systemdrive = 'undefined', host=mlinux, manualy_created='no')

        #machine 32 bits windows 7
        m = machine.objects.create(serial='1234', name='machine_windows_7_32', language = 'fr_FR')
        software.objects.create(name = 'PDFCreator', version = '1.6.2',uninstall = 'bla', host=m, manualy_created = 'no')
        software.objects.create(name = 'mozilla', version = '24.0.1',uninstall = 'bla', host=m, manualy_created = 'no')
        software.objects.create(name = 'mozilla-beta', version = '24.0.1.a',uninstall = 'bla', host=m, manualy_created = 'no')
        software.objects.create(name = 'Java 8 Update 171', version = '8.0.1710.11',uninstall = 'bla', host=m, manualy_created = 'no')
        software.objects.create(name = 'Java 8 Update 181', version = '8.0.1810.13',uninstall = 'bla', host=m, manualy_created = 'no')
        #software.objects.create(name = 'Java 8 Update 191', version = '8.0.1910.12',uninstall = 'bla', host=m, manualy_created = 'no')
        osdistribution.objects.create(name = 'Microsoft Windows 7', version = 'sp1', arch = '32bits', systemdrive = 'c', host=m, manualy_created='no')
        
        #machine 64 bits windows 7
        m64 = machine.objects.create(serial='1234', name='machine_windows_7_64')
        software.objects.create(name = 'PDFCreator', version = '1.6.2',uninstall = 'bla', host=m64, manualy_created = 'no')
        software.objects.create(name = 'mozilla', version = '24.0.1',uninstall = 'bla', host=m64, manualy_created = 'no')
        software.objects.create(name = 'mozilla-beta', version = '24.0.1.a',uninstall = 'bla', host=m64, manualy_created = 'no')
        #software.objects.create(name = 'Java 8 Update 171 (64-bit)', version = '8.0.1710.11',uninstall = 'bla', host=m64, manualy_created = 'no')
        #software.objects.create(name = 'Java 8 Update 181 (64-bit)', version = '8.0.1810.13',uninstall = 'bla', host=m64, manualy_created = 'no')
        #software.objects.create(name = 'Java 8 Update 191 (64-bit)', version = '8.0.1910.12',uninstall = 'bla', host=m64, manualy_created = 'no')
        osdistribution.objects.create(name = 'Microsoft Windows 7', version = 'sp1', arch = '64bits', systemdrive = 'c', host=m64, manualy_created='no')

        # packages with language condition
        package_test_fr_FR = package.objects.create(name = 'fr_FR', description = 'install si fr_FR', command = 'rem')
        condition_test_fr_FR = packagecondition.objects.create(name = 'fr_FR', softwarename = 'fr_FR', depends = 'language_is')
        package_test_fr_FR.conditions.add(condition_test_fr_FR)
        package_test_fr_FR.save()

        # Packages without Joker and lower condition
        package_pdf171 = package.objects.create(name = 'PDFCreator 1.7.1', description = 'install PDFCreator 1.7.1', command = 'rem')
        condition_lowerpdf171 = packagecondition.objects.create(name = 'install if PDFCreator < 1.7.1', softwarename = 'PDFCreator', softwareversion = '1.7.1',depends = 'lower')
        package_pdf171.conditions.add(condition_lowerpdf171)
        package_pdf171.save()
        
        package_pdf162 = package.objects.create(name = 'PDFCreator 1.6.2', description = 'install PDFCreator 1.6.2', command = 'rem')
        condition_lowerpdf162 = packagecondition.objects.create(name = 'install if PDFCreator < 1.6.2', softwarename = 'PDFCreator', softwareversion = '1.6.2',depends = 'lower')
        package_pdf162.conditions.add(condition_lowerpdf162)
        package_pdf162.save()

        package_moz25 = package.objects.create(name = 'mozilla 25', description = 'install mozilla 25', command = 'rem')
        condition_lowermoz25 = packagecondition.objects.create(name = 'install mozilla if < 25', softwarename = 'mozilla', softwareversion = '25',depends = 'lower')
        package_moz25.conditions.add(condition_lowermoz25)
        package_moz25.save()

        package_moz17 = package.objects.create(name = 'mozilla 17', description = 'install mozilla 17', command = 'rem')
        condition_lowermoz17 = packagecondition.objects.create(name = 'install mozilla if < 17', softwarename = 'mozilla', softwareversion = '17',depends = 'lower')
        package_moz17.conditions.add(condition_lowermoz17)
        package_moz17.save()

        package_moz24b = package.objects.create(name = 'mozilla 24 beta b', description = 'install mozilla 24 beta b', command = 'rem')
        condition_lowermoz24b = packagecondition.objects.create(name = 'install mozilla if < 24.0.1.b', softwarename = 'mozilla-beta', softwareversion = '24.0.1.b',depends = 'lower')
        package_moz24b.conditions.add(condition_lowermoz24b)
        package_moz24b.save()

        # Packages with higher condition
        package_moz17 = package.objects.create(name = 'mozilla 17 higher', description = 'install mozilla 17', command = 'rem')
        condition_moz17 = packagecondition.objects.create(name = 'install mozilla if installed and > 24.a', softwarename = 'mozilla-beta', softwareversion = '24.a',depends = 'higher')
        package_moz17.conditions.add(condition_moz17)
        package_moz17.save()
        
        package_pdf162h = package.objects.create(name = 'PDFCreator 1.6.2 higher', description = 'install PDFCreator 1.6.2', command = 'rem')
        condition_higherpdf162 = packagecondition.objects.create(name = 'install if PDFCreator >= 1.6.1', softwarename = 'PDFCreator', softwareversion = '1.6.1',depends = 'higher')
        package_pdf162h.conditions.add(condition_higherpdf162)
        package_pdf162h.save()

        # Packages with higher condition and joker
        jpackage_moz17 = package.objects.create(name = 'jmozilla 17 higher', description = 'install mozilla 17', command = 'rem')
        jcondition_moz17 = packagecondition.objects.create(name = 'install mozilla*beta if installed and > 24.a', softwarename = 'mozilla*beta', softwareversion = '24.a',depends = 'higher')
        jpackage_moz17.conditions.add(jcondition_moz17)
        jpackage_moz17.save()

        jpackage_java181h = package.objects.create(name = 'Java 181 higher', description = 'install Java 181 depend app', command = 'rem')
        jcondition_higherjava181 = packagecondition.objects.create(name = 'install if Java >= 181', softwarename = 'Java 8 Update *', softwareversion = '8.0.1810.12',depends = 'higher')
        jpackage_java181h.conditions.add(jcondition_higherjava181)
        jpackage_java181h.save()

        jpackage_javanoverh = package.objects.create(name = 'Java 8u higher empty version', description = 'install Java 8u...', command = 'rem')
        jcondition_higherjavanover = packagecondition.objects.create(name = 'install if Java exist', softwarename = 'Java 8 Update *', softwareversion = '',depends = 'higher')
        jpackage_javanoverh.conditions.add(jcondition_higherjavanover)
        jpackage_javanoverh.save()

        # Packages with Joker and lower condition
        jpackage_pdf171 = package.objects.create(name = 'jPDFCreator 1.7.1', description = 'install PDFCreator 1.7.1', command = 'rem')
        jcondition_lowerpdf171 = packagecondition.objects.create(name = 'install if PDFCrea* < 1.7.1', softwarename = 'PDFCrea*', softwareversion = '1.7.1',depends = 'lower')
        jpackage_pdf171.conditions.add(jcondition_lowerpdf171)
        jpackage_pdf171.save()
        
        jpackage_pdf162 = package.objects.create(name = 'jPDFCreator 1.6.2', description = 'install PDFCreator 1.6.2', command = 'rem')
        jcondition_lowerpdf162 = packagecondition.objects.create(name = 'install if PDFCrea* < 1.6.2', softwarename = 'PDFCrea*', softwareversion = '1.6.2',depends = 'lower')
        jpackage_pdf162.conditions.add(jcondition_lowerpdf162)
        jpackage_pdf162.save()

        jpackage_moz25 = package.objects.create(name = 'jmozilla 25', description = 'install mozilla 25', command = 'rem')
        jcondition_lowermoz25 = packagecondition.objects.create(name = 'install moz*lla if < 25', softwarename = 'moz*lla', softwareversion = '25',depends = 'lower')
        jpackage_moz25.conditions.add(jcondition_lowermoz25)
        jpackage_moz25.save()

        jpackage_moz17 = package.objects.create(name = 'jmozilla 17', description = 'install mozilla 17', command = 'rem')
        jcondition_lowermoz17 = packagecondition.objects.create(name = 'install moz*lla if < 17', softwarename = 'moz*lla', softwareversion = '17',depends = 'lower')
        jpackage_moz17.conditions.add(jcondition_lowermoz17)
        jpackage_moz17.save()

        jpackage_moz24b = package.objects.create(name = 'jmozilla 24 beta b', description = 'install mozilla 24 beta b', command = 'rem')
        jcondition_lowermoz24b = packagecondition.objects.create(name = 'install mozilla* if < 24.0.1.b', softwarename = 'jmozilla * beta b', softwareversion = '24.0.1.b',depends = 'lower')
        jpackage_moz24b.conditions.add(jcondition_lowermoz24b)
        jpackage_moz24b.save()

        jpackage_java191 = package.objects.create(name = 'jjava 191', description = 'install java 191', command = 'rem')
        jcondition_lowerjava191 = packagecondition.objects.create(name = 'install java* if < 191', softwarename = 'Java 8 Update *', softwareversion = '8.0.1910.12',depends = 'lower')
        jpackage_java191.conditions.add(jcondition_lowerjava191)
        jpackage_java191.save()

        jpackage_java191noprev = package.objects.create(name = 'jjava 191 noprev empty version', description = 'install java 191 if no previous version', command = 'rem')
        jcondition_lowerjava191noprev = packagecondition.objects.create(name = 'install java* if no previous version', softwarename = 'Java 8 Update *', softwareversion = '',depends = 'lower')
        jpackage_java191noprev.conditions.add(jcondition_lowerjava191noprev)
        jpackage_java191noprev.save()

        # package with condition arch 32bits
        package_arch32 = package.objects.create(name = 'arch32', description = 'install if 32bits', command = 'rem')
        condition_arch32 = packagecondition.objects.create(name = 'install if 32bits', softwarename = 'undefined', softwareversion = 'undefined',depends = 'is_W32_bits')
        package_arch32.conditions.add(condition_arch32)
        package_arch32.save()

        # package with condition arch 64bits
        package_arch64 = package.objects.create(name = 'arch64', description = 'install if 64bits', command = 'rem')
        condition_arch64 = packagecondition.objects.create(name = 'install if 64bits', softwarename = 'undefined', softwareversion = 'undefined',depends = 'is_W64_bits')
        package_arch64.conditions.add(condition_arch64)
        package_arch64.save()

        # package with lower and arch32 condition
        lower_arch32 = package.objects.create(name = 'lower_arch32', description = 'install if 32bits and lowerpdf171', command = 'rem')
        lower_arch32.conditions.add(condition_arch32)
        lower_arch32.conditions.add(condition_lowerpdf171)
        lower_arch32.save()

        # package with lower and arch64 condition
        lower_arch64 = package.objects.create(name = 'lower_arch64', description = 'install if 64bits and lowerpdf171', command = 'rem')
        lower_arch64.conditions.add(condition_arch64)
        lower_arch64.conditions.add(condition_lowerpdf171)
        lower_arch64.save()

        # package with condition system_is Microsoft Windows 7 
        package_MS7 = package.objects.create(name = 'MS7', description = 'install if Microsoft Windows 7', command = 'rem')
        condition_MS7 = packagecondition.objects.create(name = 'install if Microsoft Windows 7', softwarename = 'Microsoft Windows 7', softwareversion = 'undefined',depends = 'system_is')
        package_MS7.conditions.add(condition_MS7)
        package_MS7.save()

        # package with condition system_is Microsoft Windows 7 
        jpackage_MS7 = package.objects.create(name = 'jMS7', description = 'install if Microsoft *', command = 'rem')
        jcondition_MS7 = packagecondition.objects.create(name = 'install if Microsoft *', softwarename = 'Microsoft Windows *', softwareversion = 'undefined',depends = 'system_is')
        jpackage_MS7.conditions.add(jcondition_MS7)
        jpackage_MS7.save()

        # package with condition system_isnot Microsoft Windows 7
        package_MS7not = package.objects.create(name = 'MS7not', description = 'install if Microsoft Windows 7', command = 'rem')
        condition_MS7not = packagecondition.objects.create(name = 'install if Microsoft Windows 7', softwarename = 'Microsoft Windows 7', softwareversion = 'undefined',depends = 'system_not')
        package_MS7not.conditions.add(condition_MS7not)
        package_MS7not.save()

        # package with condition system_isnot Microsoft Windows 7
        jpackage_MS7not = package.objects.create(name = 'jMS7not', description = 'install if Microsoft *', command = 'rem')
        jcondition_MS7not = packagecondition.objects.create(name = 'install if Microsoft *', softwarename = 'Microsoft Windows *', softwareversion = 'undefined',depends = 'system_not')
        jpackage_MS7not.conditions.add(jcondition_MS7not)
        jpackage_MS7not.save()


    def test_lower_condition_without_joker(self):
        m = machine.objects.get(name = 'machine_windows_7_32')
        pdf171 = package.objects.get(name = 'PDFCreator 1.7.1')
        pdf162 = package.objects.get(name = 'PDFCreator 1.6.2')
        moz25 = package.objects.get(name = 'mozilla 25')
        moz17 = package.objects.get(name = 'mozilla 17')
        moz24b = package.objects.get(name = 'mozilla 24 beta b')

        self.assertEqual(check_conditions(m,pdf171), True)
        self.assertEqual(check_conditions(m,pdf162), False)
        self.assertEqual(check_conditions(m,moz25), True)
        self.assertEqual(check_conditions(m,moz17), False)
        self.assertEqual(check_conditions(m,moz24b), True)
    
    def test_higher_condition_without_joker(self):
        m = machine.objects.get(name = 'machine_windows_7_32')
        moz17 = package.objects.get(name = 'mozilla 17 higher')
        self.assertEqual(check_conditions(m,moz17), False)

    def test_higher_condition_with_joker(self):
        m = machine.objects.get(name = 'machine_windows_7_32')
        pdf162h = package.objects.get(name = 'PDFCreator 1.6.2 higher')
        java181h = package.objects.get(name = 'Java 181 higher')
        javanoverh = package.objects.get(name = 'Java 8u higher empty version')# New above 2.2.0

        self.assertEqual(check_conditions(m,pdf162h), True)
        self.assertEqual(check_conditions(m,java181h), True)
        self.assertEqual(check_conditions(m,javanoverh), True)
    
    def test_lang_condition(self):
        m = machine.objects.get(name = 'machine_windows_7_32')
        mlinux = machine.objects.get(name = 'mlinux')
        fr_FR = package.objects.get(name = 'fr_FR')
        self.assertEqual(check_conditions(mlinux,fr_FR), False)
        self.assertEqual(check_conditions(m,fr_FR), True)


    def test_lower_condition_with_joker(self):
        m = machine.objects.get(name = 'machine_windows_7_32')
        pdf171 = package.objects.get(name = 'jPDFCreator 1.7.1')
        pdf162 = package.objects.get(name = 'jPDFCreator 1.6.2')
        moz25 = package.objects.get(name = 'jmozilla 25')
        moz17 = package.objects.get(name = 'jmozilla 17')
        moz24b = package.objects.get(name = 'jmozilla 24 beta b')
        java191 = package.objects.get(name = 'jjava 191')
        java191noprev = package.objects.get(name = 'jjava 191 noprev empty version')

        self.assertEqual(check_conditions(m,pdf171), True)
        self.assertEqual(check_conditions(m,pdf162), False)
        self.assertEqual(check_conditions(m,moz25), True)
        self.assertEqual(check_conditions(m,moz17), False)
        self.assertEqual(check_conditions(m,moz24b), True)
        self.assertEqual(check_conditions(m,java191), True)
        self.assertEqual(check_conditions(m,java191noprev), False)
    
    def test_arch32_or_64(self):
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        m64 = machine.objects.get(name = 'machine_windows_7_64')
        arch32 = package.objects.get(name = 'arch32')
        arch64= package.objects.get(name = 'arch64')
    
        self.assertEqual(check_conditions(m32,arch32), True)
        self.assertEqual(check_conditions(m64,arch64), True)
        self.assertEqual(check_conditions(m32,arch64), False)
        self.assertEqual(check_conditions(m64,arch32), False)
    
    def test_system_is_without_joker(self):
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        mlinux = machine.objects.get(name = 'mlinux')
        pms7 = package.objects.get(name = 'MS7')
        self.assertEqual(check_conditions(m32,pms7), True)
        self.assertEqual(check_conditions(mlinux,pms7), False)

    def test_system_is_with_joker(self):
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        mlinux = machine.objects.get(name = 'mlinux')
        jpms7 = package.objects.get(name = 'jMS7')
        self.assertEqual(check_conditions(m32,jpms7), True)
        self.assertEqual(check_conditions(mlinux,jpms7), False)

    def test_system_is_not_without_joker(self):# New since 2.2.0
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        mlinux = machine.objects.get(name = 'mlinux')
        pms7 = package.objects.get(name = 'MS7not')
        self.assertEqual(check_conditions(m32,pms7), False)
        self.assertEqual(check_conditions(mlinux,pms7), True)

    def test_system_is_not_with_joker(self):# New since 2.2.0
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        mlinux = machine.objects.get(name = 'mlinux')
        jpms7 = package.objects.get(name = 'jMS7not')
        self.assertEqual(check_conditions(m32,jpms7), False)
        self.assertEqual(check_conditions(mlinux,jpms7), True)

    def test_package_with_condition_lower_arch(self):
        m32 = machine.objects.get(name = 'machine_windows_7_32')
        m64 = machine.objects.get(name = 'machine_windows_7_64')
        lower_arch32 = package.objects.get(name = 'lower_arch32')
        lower_arch64 = package.objects.get(name = 'lower_arch64')
    
        self.assertEqual(check_conditions(m32,lower_arch32), True)
        self.assertEqual(check_conditions(m64,lower_arch64), True)
        self.assertEqual(check_conditions(m32,lower_arch64), False)
        self.assertEqual(check_conditions(m64,lower_arch32), False)

