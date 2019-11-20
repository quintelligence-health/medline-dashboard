#!/usr/bin/python

# aim: prepares for ElasticSearch in Python3
# usage: python3 es_upload.py source_dir index_name_suffix

import glob
import os
import datetime
import getopt

from elasticsearch import Elasticsearch, helpers

import json

import sys

if len(sys.argv) != 3:
    sys.exit("usage: python3 es_upload.py source_dir index_name_suffix")

source_dir = sys.argv[1]  
version_suffix = sys.argv[2]  

es = Elasticsearch() 

for src_name in glob.glob(os.path.join(source_dir, '*.json')):
    print(datetime.datetime.now(), ' load: ', src_name)
    print(datetime.datetime.now(), "create index structure for InfluenzanetSet")
    with open(src_name, encoding = "utf-8") as data_file:
        data = json.load(data_file)
    print(datetime.datetime.now(), "bulk request")
    res = helpers.bulk(es, data, ignore=400, raise_on_error=False, raise_on_exception=False)
    print(res)
    print(datetime.datetime.now(), "Bulk request done")
print(datetime.datetime.now(), 'done all influenzanet files!')