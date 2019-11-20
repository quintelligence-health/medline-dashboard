#!/usr/bin/python

# this script converts CSV to JSON in Python3
# usage: python3 csv_to_json_bulk.py <<path-to-file>>/CSV <<path-to-file>>/JSON

import glob
import os
import datetime
import sys
import csv
import json

# if len(sys.argv) != 2:
#     sys.exit("usage: csv_to_json_bulk.py source_dir destination_dir index_name_suffix")

source_dir = sys.argv[1]  # '<<path-to-file>>/CSV'
destination_dir = sys.argv[2]  # '<<path-to-file>>/JSON'
meta_def = sys.argv[3]  # CSV with meta information
mapping_out_dir = sys.argv[4]  # output jsons with elastic mapping

metaInfoDict = {}


print(datetime.datetime.now(), 'load from', source_dir, 'into', destination_dir)

# Read CSV File
def  read_csv_survey(country, year, csv_rows_intake):
    csv_rows_survey = []
    survey_csv_file = os.path.join(source_dir, "survey_"+country+year+".csv")
    print("Survey file name:", survey_csv_file)
    with open(survey_csv_file, encoding="latin_1") as csv_file:
        docuemnts_total = 0
        documents_valid = 0
        reader = csv.DictReader(csv_file)
        for row in reader:
            docuemnts_total = docuemnts_total + 1
            document = {"country": country, "year": "20"+year}
            err = False
            for field_code, field_info in metaInfoDict["survey"].items():
                if field_info["mandatory"] != "fname":
                    val = None
                    if field_code in row:
                        val = row[field_code]
                    if (val is not None) & (val != ""):
                        if field_info["type"] != "ignore":
                            if field_info["type"] == "integer":
                                if(val.isdigit()):
                                    document[field_info["name"]] = val
                                else:
                                    err = True
                                    print(datetime.datetime.now(), 'ERROR integer', field_code, "=", val, "from", survey_csv_file)

                            else:
                                if field_info["type"] == "date":
                                    try:
                                        datetime.datetime.strptime(val, '%Y-%m-%d')
                                        document[field_info["name"]] = val
                                    except ValueError:
                                        err = True
                                        print(datetime.datetime.now(), 'ERROR date', field_code, "=", val, "from",
                                              survey_csv_file)
                                else:
                                    document[field_info["name"]] = val
                    else:
                        if field_info["mandatory"] == "y":
                            err = True
                            print(datetime.datetime.now(), 'ERROR mandatory', field_code, "from", survey_csv_file)
            if not err:
                if(document["uid"] in csv_rows_intake):
                    documents_valid = documents_valid + 1
                    index_intake = csv_rows_intake[document["uid"]]
                    index_document = {'_op_type': 'index', '_index': "influenzanet_survey", '_type': "survey",
                                  '_source': {"intake": index_intake['_source'], "survey": document}}
                    csv_rows_survey.append(index_document)
                else:
                    err = True
                    print(datetime.datetime.now(), 'ERROR no intake for ', document["uid"], "from", survey_csv_file)

        print("about to write ", documents_valid, "documents out of ", docuemnts_total)
        write_json(csv_rows_survey, os.path.join(destination_dir, "survey_"+country+year+".json"))



# Read CSV File
def read_csv_intake(file, json_file):
    csv_rows_intake = {}
    base = os.path.basename(file)
    document_type = base[0:6]
    country = base[7:-6]
    year = base[9:-4]
    print("File name metadata:", document_type, country, year)
    with open(file, encoding="latin_1") as csv_file:
        reader = csv.DictReader(csv_file)
        docuemnts_total=0
        documents_valid=0
        for row in reader:
            docuemnts_total=docuemnts_total+1
            document = {"country": country, "year": "20"+year}
            err = False
            for field_code, field_info in metaInfoDict[document_type].items():
                if field_info["mandatory"] != "fname":
                    val = None
                    if field_code in row:
                        val = row[field_code]
                    if (val is not None) & (val != ""):
                        if field_info["type"] != "ignore":
                            if field_info["type"] == "integer":
                                if(val.isdigit()):
                                    document[field_info["name"]] = val
                                else:
                                    err = True
                                    print(datetime.datetime.now(), 'ERROR integer', field_code, "=", val, "from", file)

                            else:
                                if field_info["type"] == "date":
                                    try:
                                        datetime.datetime.strptime(val, '%Y-%m-%d')
                                        document[field_info["name"]] = val
                                    except ValueError:
                                        err = True
                                        print(datetime.datetime.now(), 'ERROR date', field_code, "=", val, "from",
                                              file)
                                else:
                                    document[field_info["name"]] = val
                    else:
                        if field_info["mandatory"] == "y":
                            err = True
                            print(datetime.datetime.now(), 'ERROR mandatory', field_code, "from", file)
            if not err:
                documents_valid=documents_valid+1
                index_document = {'_op_type': 'index', '_index': "influenzanet_intake", '_type': document_type,
                                  '_source': document}
                csv_rows_intake[document["uid"]] = index_document
        print("about to write ", documents_valid, "documents out of ", docuemnts_total)
        write_json(list(csv_rows_intake.values()), json_file)
        read_csv_survey(country, year, csv_rows_intake)


def process_definition_csv(file):
    metaInfoDict["intake"] = {}
    metaInfoDict["survey"] = {}
    elasticMappingIntake = {"mappings": {"intake": {"properties": {}}}}
    elasticMappingSurvey = {"mappings": {"survey": {"properties": {"survey" : {"properties": {}}, "intake" : {"properties": {}}}}}}
    with open(file, encoding="utf8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            field_info = {"name": row["alt_name"], "type": row["type"], "mandatory": row["mandatory"]}
            doc_type = row["documentType"]
            field_code = row["field_unified"]
            metaInfoDict[doc_type][field_code] = field_info
            if row["type"] != "ignore":
                if doc_type=="intake":
                    elasticMappingIntake["mappings"]["intake"]["properties"][row["alt_name"]] = {"type": row["elastic_type"]}
                elasticMappingSurvey["mappings"]["survey"]["properties"][doc_type]["properties"][row["alt_name"]] = {"type": row["elastic_type"]}

        write_json(elasticMappingIntake, os.path.join(mapping_out_dir, "influenzanet_intake.json"))
        write_json(elasticMappingSurvey, os.path.join(mapping_out_dir, "influenzanet_survey.json"))

        # Convert csv data into json and write it


def write_json(data, json_file):
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))


def convert_all_csv():
    for src_name in glob.glob(os.path.join(source_dir, 'intake_*.csv')):
        base_out = os.path.basename(src_name)[:-3] + 'json'
        output_file = os.path.join(destination_dir, base_out)

        print(datetime.datetime.now(), ' convert: ', src_name, output_file)
        read_csv_intake(src_name, output_file)


process_definition_csv(meta_def)
convert_all_csv()
print(datetime.datetime.now(), 'done!')
