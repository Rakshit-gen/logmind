# Postmortem: inventory-svc cache stampede

**Date:** 2025-11-02
**Duration:** 15 minutes
**Services affected:** inventory-svc

## Summary

A cache key used by every product page expired at the same instant for
every instance (it was set with a fixed TTL and every instance had
started around the same time). All instances hit the database for the
same query simultaneously, which spiked database CPU and slowed every
other query on that database for about fifteen minutes.

## Root cause

Fixed TTL cache with no jitter, plus correlated instance start times from
a rolling deploy that happened to finish close together.

## Fix

Added random jitter to the TTL so cache entries expire at different
times across instances.

## Follow-up

Same TTL pattern exists in two other services. Worth a sweep to check for
the same fixed-TTL, no-jitter pattern elsewhere.
