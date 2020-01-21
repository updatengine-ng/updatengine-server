- 'section_end': Obsolete. Was used to split the commands from options.
- 'download_no_restart': Initialy it stopped the deployment loop after the first run even if all was not succedeed. Indeed sometimes some conditions produced infinite loop because some upgrades was not returned in inventory or conditions are incorrects. Since 3.1, it is only applied on the affected package and this one is executed only one time on a deployment phase.
- 'no_break_on_error': By default, without this option, if a package installation failed then the overall deployment process is stopped at this point. With this option it continues anyway with the following package.
- 'install_timeout_X': By default, each package has an installation timeout of 30 minutes. With this option, a timeout of X seconds is set for the package to which it is applied.

