# Postmortem: checkout-api 500s from payments-api timeout

**Date:** 2026-03-14
**Duration:** 22 minutes
**Services affected:** checkout-api, payments-api

## Summary

checkout-api started returning 500s to customers. The root cause was a
deploy to payments-api that lowered its connection pool size from 50 to
10, which was fine under normal load but exhausted almost immediately
during the morning traffic peak. checkout-api's calls to payments-api
started timing out, and checkout-api does not have a retry or circuit
breaker around that call, so every failed payments-api call became a
customer-facing 500.

## Root cause

The connection pool change was in the same deploy as an unrelated logging
change and nobody flagged it in review because the diff was buried in a
config file that does not usually get touched.

## Fix

Reverted the pool size change. Added an alert on payments-api connection
pool saturation so this shows up before it becomes customer-facing.

## Follow-up

checkout-api still doesn't have a circuit breaker on the payments-api
call. That's tracked separately and hasn't shipped yet.
