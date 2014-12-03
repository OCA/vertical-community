# Account Wallet #
Allow each partners to have a wallet linked to their account, and to make transactions between them.

## Functions ##
1. Transactions between partners
1. Based on accounting entries
1. Multi-currency and configurable account chart
1. Limits management
1. Display balances on the partner record, with possible override of limit and accounts used

## Created Views ##
- * INHERIT account.wallet.transaction.form.admin (form)
- * INHERIT community.configuration.wallet (form)
- * INHERIT partner.form.wallet (form)
- account.wallet.config.currency.form (form)
- account.wallet.config.currency.tree (tree)
- account.wallet.currency.line.tree (tree)
- account.wallet.transaction.form (form)
- account.wallet.transaction.search (search)
- account.wallet.transaction.tree (tree)
- res.partner.wallet.currency.form (form)
- res.partner.wallet.currency.tree (tree)

## Dependencies ##
- account_accountant	
- account_reversal	
- base_community	

## Created Menus ##
- Accounting/Transactions
- Accounting/Transactions/All
- Accounting/Transactions/My transactions
 
## Defined Reports ##
- This module does not create report.