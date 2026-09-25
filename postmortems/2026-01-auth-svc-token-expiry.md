# Postmortem: auth-svc mass logout from clock drift

**Date:** 2026-01-09
**Duration:** 40 minutes
**Services affected:** auth-svc, all downstream services

## Summary

A subset of auth-svc instances had clock drift of about six minutes after
an underlying host migration. Token expiry checks on those instances
rejected valid tokens as expired, which looked like a mass logout to
users hitting those specific instances.

## Root cause

The new host pool did not have NTP configured correctly after migration.
This was not caught because our health checks don't verify system clock
accuracy, only that the process responds.

## Fix

Fixed NTP config on the new host pool and rolled the bad instances.
Added a clock drift check to the auth-svc health endpoint.

## Follow-up

None of the affected instances threw errors, they just rejected valid
tokens, which is why this took longer to diagnose than it should have.
Worth adding an explicit metric for token rejection rate by instance.
