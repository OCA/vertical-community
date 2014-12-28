# Mail for Holocracy #

This module enhances the mail.group object in order to use it for holocracy processes and nesting message groups into each other.

## Functions ##
- Mail.group is now a recursive model. You can't subscribe to a parent group but each followers of a group is automatically subscribed to his parent group
- A group can now be a normal group, a circle or a role
- In a circle, you can define permissions for children groups
- A group can now be linked to a partner, you can easily create it from the group


> Holacracy is a social technology or system of organizational governance in which authority and decision-making are distributed throughout a fractal holarchy of self-organizing teams rather than being vested at the top of a hierarchy.[1] Holacracy has been adopted in for-profit and non-profit organizations in the U.S., France, Germany, New Zealand, Australia, and the UK.

link to  Wikipedia: [http://en.wikipedia.org/wiki/Holacracy](http://en.wikipedia.org/wiki/Holacracy)

## Created Views ##
- INHERIT mail.group.form.holacracy (form)
- INHERIT mail.group.tree.extension (tree)
- INHERIT partner.form.holacracy (form)
- mail.group.tree.tree (tree)

## Dependencies ##
- base_community		vc
- base_recursive_model	ext
- mail
	
## Created Menus ##
- Messaging/My Groups/Groups list

## Defined Reports ##
- This module does not create report.
