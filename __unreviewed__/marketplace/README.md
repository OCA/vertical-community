# Marketplace #
Implement a marketplace so users can exchange goods and services

## Functions ##
- Manage announcement (Offer and Demand)
- Make proposition with a complex acceptation and payment workflow
- Pay in any currency available in wallet
- Manage category and skills 

## Created Views ##
- * INHERIT marketplace.announcement.form.admin (form)
- * INHERIT marketplace.proposition.form.admin (form)
- * INHERIT partner.form.wallet.marketplace (form)
- marketplace.announcement.category.form (form)
- marketplace.announcement.category.tree (tree)
- marketplace.announcement.form (form)
- marketplace.announcement.search (search)
- marketplace.announcement.tree (tree)
- marketplace.proposition.form (form)
- marketplace.proposition.search (search)
- marketplace.proposition.tree (tree)
- marketplace.tag.form (form)
- marketplace.tag.tree (tree)

## Dependencies ##
- account		
- account_accountant		
- account_wallet		vc
- base	
- base_recursive_model	vc
- vote					vc
	
## Created Menus ##
- Marketplace
- Marketplace/Configuration
- Marketplace/Configuration/Offers/Wants Categories
- Marketplace/Configuration/Offers/Wants Tags
- Marketplace/Moderation
- Marketplace/Moderation/Transactions in dispute
- Marketplace/My Market
- Marketplace/My Market/As Asker
- Marketplace/My Market/As Asker/My payments
- Marketplace/My Market/As Asker/My replies to others
- Marketplace/My Market/As Asker/My wants
- Marketplace/My Market/As Asker/Offers to follow
- Marketplace/My Market/As Asker/Propositions from others
- Marketplace/My Market/As Bringer
- Marketplace/My Market/As Bringer/My Offers
- Marketplace/My Market/As Bringer/My cashing
- Marketplace/My Market/As Bringer/My propositions to others
- Marketplace/My Market/As Bringer/Replies from others
- Marketplace/My Market/As Bringer/Wants to follow
- Marketplace/My Market/Ongoing
- Marketplace/My Market/Ongoing/My transactions in moderation
- Marketplace/My Market/Ongoing/Payments to confirm
- Marketplace/My Market/Ongoing/Propositions to accept
- Marketplace/My Market/Ongoing/Replies to accept
- Marketplace/The Market
- Marketplace/The Market/Offers
- Marketplace/The Market/Offers/All
- Marketplace/The Market/Offers/Per category
- Marketplace/The Market/Offers/Per location
- Marketplace/The Market/Transactions
- Marketplace/The Market/Transactions/All
- Marketplace/The Market/Transactions/Per category
- Marketplace/The Market/Transactions/Per location
- Marketplace/The Market/Wants
- Marketplace/The Market/Wants/All
- Marketplace/The Market/Wants/Corresponding to my skills
- Marketplace/The Market/Wants/Per category
- Marketplace/The Market/Wants/Per location

## Defined Reports ##
- This module does not create report.