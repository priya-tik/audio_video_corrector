#!/usr/bin/env python3

with open("sync_target.txt") as f:
    fixed = f.read().strip()

if fixed == "presenter":
    print("flavor=presenter/work")
elif fixed == "presentation":
    print("flavor=presentation/work")
else:
    print("flavor=sync/error")
