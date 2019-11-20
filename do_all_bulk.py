import glob
import os
import xml.etree.ElementTree as ET
import datetime
import sys
from elasticsearch import Elasticsearch, helpers

if len(sys.argv) != 3:
    sys.exit("usage: do_all_bulk.py source_dir index_name_suffix")

es = Elasticsearch()

source_dir = sys.argv[1] 
version_suffix = sys.argv[2] 

print(datetime.datetime.now(), 'load from', source_dir)

for src_name in glob.glob(os.path.join(source_dir, '*.xml')):
    base = os.path.basename(src_name)
    print(datetime.datetime.now(), ' load: ', src_name)
    treeXML = ET.parse(src_name)
    rootXML = treeXML.getroot()
    print(datetime.datetime.now(), "create index structure")
    if(rootXML.tag != "PubmedArticleSet"):
        print("Warning: root element is ", rootXML.tag)
    else:
        documents = []
        for pubMedArticleXML in rootXML:
            if(pubMedArticleXML.tag != "PubmedArticle"):
                print("Warning: child element is ", pubMedArticleXML.tag)
            else:
                medlineCitationXML = pubMedArticleXML.find("MedlineCitation")
                if(medlineCitationXML == None):
                    print("Warning: No  MedlineCitation")
                else:
                    dateCompletedXML = medlineCitationXML.find("DateCompleted")
                    if(dateCompletedXML == None):
                        print("Warning: skip - not completed. PMID=", medlineCitationXML.find("PMID").text)
                    else:
                        indexDocument = {}
                        document = {}
                        indexDocument['_op_type'] = 'index'
                        indexDocument['_index'] = "PubmedArticleSet".lower() + version_suffix
                        indexDocument['_type'] = "PubmedArticle".lower()
                        indexDocument['_id'] = medlineCitationXML.find("PMID").text
                        indexDocument['_source'] = document
                        documents.append(indexDocument)
                        document["PMID"] = medlineCitationXML.find("PMID").text
                        articleXML = medlineCitationXML.find("Article")
                        document["PubModel"] = articleXML.get("PubModel")
                        #TODO parse formatted text
                        document["ArticleTitle"] = articleXML.find("ArticleTitle").text
                        #TODO parse formatted text
                        abstractXML = articleXML.find("Abstract")
                        if(abstractXML != None):
                            abstractContent = ""
                            for abstractChildXML in abstractXML:
                                if(abstractContent != ""):
                                    abstractContent += "\n"
                                labelXML = abstractChildXML.get("Label")
                                nlmCategory = abstractChildXML.get("NlmCategory")
                                if(labelXML != None):
                                    abstractContent += labelXML
                                    if(nlmCategory != None):
                                        abstractContent += " / "
                                if (nlmCategory != None):
                                    abstractContent += nlmCategory
                                if(abstractChildXML.text != None):
                                    if(abstractContent != ""):
                                        abstractContent += ": "
                                    abstractContent += abstractChildXML.text
                                else:
                                    print("Abstract contenct null for ", document["PMID"])
                            document["Abstract"] = abstractContent

                        authorListXML = articleXML.find("AuthorList")
                        if(authorListXML != None):
                            document["AuthorList"] = []
                            for authorXML in authorListXML:
                                authorFull = []
                                for authorChildXML in authorXML:
                                    authorFull.append(authorChildXML.text)
                                document["AuthorList"].append(','.join(map(str, authorFull)))

                        document["Language"] = articleXML.find("Language").text
                        y=dateCompletedXML.find("Year").text
                        m=dateCompletedXML.find("Month").text
                        d=dateCompletedXML.find("Day").text
                        dateCompleted = y+"-"+m+"-"+d
                        document["DateCompleted"] = dateCompleted
                        document["MedlineJournalInfo"] = {}
                        medlineJournalInfoXML = medlineCitationXML.find("MedlineJournalInfo")
                        for medlineJournalInfoElementXML in medlineJournalInfoXML:
                            document["MedlineJournalInfo"][medlineJournalInfoElementXML.tag] = medlineJournalInfoElementXML.text

                        document["ChemicalList"] = []
                        chemicalListXML = medlineCitationXML.find("ChemicalList")
                        if (chemicalListXML != None):
                            for chemicalXML in chemicalListXML:
                                chemical = {}
                                document["ChemicalList"].append(chemical)
                                chemical["RegistryNumber"] = chemicalXML.find("RegistryNumber").text
                                chemical["NameOfSubstance"] = chemicalXML.find("NameOfSubstance").text
                                chemical["UI"] = chemicalXML.find("NameOfSubstance").get("UI")

                        document["MeshHeadingList"] = []
                        meshHeadingListXML = medlineCitationXML.find("MeshHeadingList")
                        if(meshHeadingListXML != None):
                            for meshHeadingXML in meshHeadingListXML:
                                meshHeading = {}
                                document["MeshHeadingList"].append(meshHeading)
                                for k, v in meshHeadingXML.find("DescriptorName").items():
                                    meshHeading[k] = v
                                meshHeading["desc"] = meshHeadingXML.find("DescriptorName").text
                                meshHeading["QualifierNameList"] = []
                                for qualifierNameXML in meshHeadingXML.findall("QualifierName"):
                                    qualifierName={}
                                    meshHeading["QualifierNameList"].append(qualifierName)
                                    for k, v in qualifierNameXML.items():
                                        qualifierName[k] = v
                                    qualifierName["desc"] = qualifierNameXML.text

        print(datetime.datetime.now(), "bulk request")
        res = helpers.bulk(es, documents, ignore=400, raise_on_error=False, raise_on_exception=False)
        print(res)
        print(datetime.datetime.now(), "Bulk request done")
print(datetime.datetime.now(), 'done!')
