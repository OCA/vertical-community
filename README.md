# Odoo for Communities Verticalization #
The OCA Communities Verticalizations project is a collaborative effort to develop a robust, commercial-grade, set of apps to transform odoo into a full featured platform for communities.
The project is managed by a growing worldwide community of volunteers that are willing to contribute to the development and documentation to make this vision real.

## About ##
Communities Verticalizations provides solutions to manages a wide range of needs of collaborative project and organisations. It bundles helpful existing odoo apps as Blog, Forum together with new modules to finally get a versatile and interconnected selection of community related apps.
The new apps are covering almost any basic needs to manage many types of ressurces in Non Profit Organisations. So it includes apps for Crowdfunding, Coworking, Complementary Currencies and a powerful Marketplace. The currency (eWallet) modules are fully integrated into the financial part of odoo so it allows to perform many financial and monetary actions. You can use it for issuing currencies, paying resources from the marketplace or a shop, sending/receiving digital cash aso.. Because the eWallet is able to handle multi-currencies, the framework is open to include other transaction engines as Cyclos or Cryptocurrency framework one day.

## Contributing ##
If you are interested by this project, please join the mailing-list: https://launchpad.net/~odoo-communitytools-team

Contributions are welcome. Please read the guidelines of the OCA : http://odoo-community.org/page/website.how-to

**Translations:**<br>Please use for the translations the translation section on launchpad:
https://translations.launchpad.net/odoo-vertical-community

**Temporary process:**<br>
Currently we have a dozen of modules to include in the OCA repo which are not reviewed yet. Reviewing it will take time and we can't stop develop on them during that time.
Theses modules are under the "__unreviewed__" directory and must not be already considered OCA quality.

The modules will be reviewed one by one, when a module is ready to be reviewed it will be pushed out of "__unreviewed__" directory through a merge request.
Every commit concerning a module already reviewed shall respect the OCA guidelines.
Every commit which concern only modules in __unreviewed__ directory shall be marked with [UNREVIEWED] tag and is allowed to be directly merge without respecting the two reviewers rule.

This is only a temporary process until all modules are reviewed. No modules other than the current ones shall be accepted inside __unreviewed__ directory.

# Installation #
Installation process is at present stage only possible in manual way.
## Prerequisite ##
Before installing the module make sure that the you have configured an addon path for custom addons. In a Linux system the parameter in the config file usually looks similar as the following example:
 specify additional addons paths (separated by commas)
addons_path = /opt/odoo/odoo-server/addons, /opt/odoo/custom/addons
In this case you have to install the modules into /opt/odoo/custom/addons. At the present stage on dependency could not automatically resolved so you have to install one extra module that vertical community depends on. This module is available from the Github repository of OCA.<br><br>
git clone https://github.com/OCA/account-financial-tools.git<br><br>
and the community modules itselfs:
git clone https://github.com/OCA/vertical-community.git<br><br>
from the downloaded repo you have to copy now the account_reversal module from the financial tools and all the modules in vertical-community / __unreviewed__ / from the vertical community into the addon directory.
## Installing the modules ##
Then go to you odoo webinterface to the module section and start "Update module list". Then look for the "Odoo for Communities" and the marketplace module and install them.
We hope you enjoy checking out what all you can do with this apps. But remember the modules are still in a Testing/Beta phase.
