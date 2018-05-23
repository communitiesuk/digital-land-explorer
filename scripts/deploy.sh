#!/bin/bash

set -e

if [ -n "$CF_USERNAME" ] && [ -n "$CF_PASSWORD" ]; then
  cf login -a "$CF_API" -u "$CF_USERNAME" -p "$CF_PASSWORD"
fi

cf target -o "$ORG" -s "$SPACE"

cf push

cf run-task digital-land-explorer "flask db upgrade" --name db-upgrade

