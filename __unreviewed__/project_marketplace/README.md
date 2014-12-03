# Marketplace for Project #
**Link project to the marketplace**

## Functions ##
- Publish your task in the marketplace to find someone which will do it
- When a proposition is accepted, a task is automatically created for him
- Modify task assignment to use partner from the marketplace

## Created Views ##
- * INHERIT marketplace.announcement.form.project (form)
- * INHERIT marketplace.proposition.form.project (form)
- * INHERIT project.assigned.partner.config.tree.marketplace (tree)
- * INHERIT project.task.form.marketplace (form)
- * INHERIT project.task.type.form.marketplace (form)

## Dependencies ##
marketplace				vc
project	
project_assignment

## Created Menus ##
- This module does not create menu.

## Defined Reports ##
- This module does not create report.