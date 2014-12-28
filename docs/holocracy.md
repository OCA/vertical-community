# Holocracy/Messaging Apps#

This module enhances the mail.group object in order to use it for holocracy processes and nesting message groups into each other. 

## Functions ##
- Group Messaging is now a recursive application. You can't subscribe to a parent group but each followers of a group is automatically subscribed to his parent group
- A group can now be a normal group, a circle or a role
- In a circle, you can define permissions for children groups
- A group can now be linked to a partner, you can easily create it from the group

## Theory ##
- Discussion Group are only for talk matters without any specific rights
- Circle Group can have specific wallet and several rights spread between roles
- Roles Group are child of Circle Group and inherit or not rights from them.
- Members who followed a group will inherit his rights

![mail_holocracy](https://cloud.githubusercontent.com/assets/2928740/5514942/c485d492-8853-11e4-8c6d-4c66c5cc26cc.png)
## Example ##
Company CA-Technology:
Within the module CA-Technology is a circle which represent a company with several roles and circles inside. This main circle own a wallet for all the company. Wallet control is owned by the board role.

1. Designer circle group people involved in design.
1. Board role have several rights it can control wallet, invitation and group management. 
1. Engineering circle group people involved in technical matters. It have a specific wallet which is controlled by treasury role. Please not that this circle have his own circles and roles.
Member Aurélie follow engineering circle, design circle and board role. That means she follow project and discussion from engineering and design. But she also can control CA-Technology wallet as a member of Board role. Thus during transactions she can use wallet for CA-Technology.

## Use ##
To access the settings of the Holocracy functions you have to enter the following menu:

Messaging/My Groups/Join a Group

Odoo comes with two predefined groups. You can change on of this existing groups or create a new one. The following example shows a group called Organisations who is defined as a circle group. Circles Group goal is to spread leadership and responsibility to roles.
There are three (child) organisations defined. And each of them is a circle.

![holocracy-join a group 2 - odoo](https://cloud.githubusercontent.com/assets/2928740/5515007/89aa9274-8856-11e4-8391-52f9effd3015.png)

----------

**The following view shows the child organisation My Company.** <br>
**(Childs Section)** A list of roles in this company.<br>
**(Partner Section)** Is a list of partner related contacts.

![holocracy-join a group 3 - odoo](https://cloud.githubusercontent.com/assets/2928740/5515008/92ced04a-8856-11e4-8d5b-ec4951a694fb.png)
At the end is the standard Messaging section.


----------



> Holacracy is a social technology or system of organizational governance in which authority and decision-making are distributed throughout a fractal holarchy of self-organizing teams rather than being vested at the top of a hierarchy.[1] Holacracy has been adopted in for-profit and non-profit organizations in the U.S., France, Germany, New Zealand, Australia, and the UK.

link to Wikipedia article: [http://en.wikipedia.org/wiki/Holacracy](http://en.wikipedia.org/wiki/Holacracy)

