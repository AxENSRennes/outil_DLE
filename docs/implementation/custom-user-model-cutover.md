# Custom User Model Cutover

Story 1.2 changes the Django user baseline from the implicit `auth.User` table to the explicit `authz.User` model.

## When This Applies

Use this cutover if an environment was already initialized from the Story 1.1 foundation before Story 1.2 was applied.

Typical examples:

- an existing local developer database
- a shared dev database
- a UAT database created before the `authz` migrations existed

## Required Rule

Do not point an already-initialized environment at the Story 1.2 code until one of the cutover paths below has been completed.

## Preferred Path for Foundation Environments

This project is still in its platform-foundation phase and does not yet carry regulated business data. For dev and early UAT environments, the preferred cutover is a clean rebuild:

1. Stop application processes that connect to the database.
2. Back up the database if you need to preserve local test accounts for reference.
3. Drop and recreate the database.
4. Run migrations from the current codebase.
5. Recreate the required admin, test, or demo users in `authz_user`.

## Preservation Path for Existing Accounts

If existing local or UAT accounts must be preserved:

1. Export the required user records from `auth_user` before the cutover.
2. Recreate those accounts through Django using the current `authz.User` model after the new schema is migrated.
3. Reassign any site-role memberships in `authz.SiteRoleAssignment`.
4. Validate login and admin access before reopening the environment to other users.

## Not Supported

- In-place reuse of legacy `auth_user` rows without an explicit migration or recreation step
- Assuming Django will transparently map old `auth_user` data into `authz_user`
- Production rollout without rehearsing the chosen cutover path first
