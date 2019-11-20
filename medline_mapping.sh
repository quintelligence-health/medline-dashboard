#!/bin/bash

curl -XDELETE "<location of pubmedarticleset001?pretty>"
curl -H "Content-Type: application/json" -XPUT "<location of pubmedarticleset001?pretty>" -d @pubmedarticleset_mapping.json