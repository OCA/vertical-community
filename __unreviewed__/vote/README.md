# Vote API #
**Framework module for managing vote inside Odoo**

## Functions ##
- Vote type configurable
- Use base inherit config to modify vote types in category
- Provide abstract class for implementing vote in your own classes
- Votes are visible in object marked as "evaluated"

## Created Views ##
- * INHERIT community.configuration.vote (form)
- * INHERIT partner.form.vote (form)
- * INHERIT vote.vote.form.admin (form)
- vote.config.line.form (form)
- vote.config.line.tree (tree)
- vote.type.form (form)
- vote.type.tree (tree)
- vote.vote.evaluated.form (form)
- vote.vote.evaluated.tree (tree)
- vote.vote.form (form)
- vote.vote.line.tree (tree)
- vote.vote.tree (tree)

## Dependencies ##
base	
base_community			vc
base_recursive_model	vc
membership_users

## Created Menus ##
- Association/Configuration/Vote
- Association/Configuration/Vote/Vote types

## Defined Reports ##
- This module does not create report.