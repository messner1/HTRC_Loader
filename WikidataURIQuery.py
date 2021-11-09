'''
Queries Wikidata for the identifier URIs of unique authors found in a wordsbyyear generated dataset. Uses two search methods: an "exact match" and a free text search interface.
Returns a JSON file of authors with all of their possible URIs, which can be processed further for advanced information.
infile
Inputs: JSON words file
Outputs: JSON
Author: Craig Messner
'''

from pathlib import Path
import argparse
import json
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator.wbi_config import config

config['BACKOFF_MAX_TRIES'] = 5

exact_query = '''
SELECT DISTINCT ?item ?label
WHERE
{{
  SERVICE wikibase:mwapi
  {{
    bd:serviceParam wikibase:endpoint "www.wikidata.org";
                      wikibase:api "EntitySearch";
                      mwapi:search "{auth_name}";
                      mwapi:language "en".
    ?item wikibase:apiOutputItem mwapi:item.
  }}
  ?item rdfs:label ?label. FILTER( LANG(?label)="en" )

#person, occupation subclass of author

    ?item wdt:P31 wd:Q5;
     #wdt:P106 wd:Q36180 ;
     wdt:P106/wdt:P279 wd:Q482980.

}}

'''

search_query = '''
SELECT DISTINCT ?item ?label
WHERE
{{
  SERVICE wikibase:mwapi
  {{
    bd:serviceParam wikibase:endpoint "www.wikidata.org";
                    wikibase:api "Generator";
                    mwapi:generator "search";
                    mwapi:gsrsearch "inlabel:{auth_name}"@en;
                    mwapi:gsrlimit "max".
    ?item wikibase:apiOutputItem mwapi:title.
  }}
  ?item rdfs:label ?label. FILTER( LANG(?label)="en" )

#person, occupation subclass of author
  
    ?item wdt:P31 wd:Q5;
     #wdt:P106 wd:Q36180 ;
     wdt:P106/wdt:P279 wd:Q482980.
  
   
}}

'''

def format_author(author):
    a_split = [n for n in author.split(',') if n is not '']
    try:
        given = a_split[1]
        family = a_split[0]
        given = given.strip()
        given = given.rstrip()
        family = family.strip()

        #remove periods from non initials
        if given[-1] == '.' and not given[-2].isupper():
            given = ''.join(given[0:-1])

        return given + ' ' + family

    except IndexError:
        return author




def main(infile, outfile):
    author_out = {}
    with infile.open(encoding='utf-8') as dataIn:
         di = json.load(dataIn)

         for author in di.keys():
            formatted_name = format_author(author)
            if formatted_name is not None:
                try:
                    a1 = exact_query.format(auth_name=formatted_name)
                    res = execute_sparql_query(a1, max_retries=5)
                    #print(res)

                    author_out[author] = {'formatted_name': formatted_name, 'wikidata_obj': res, 'prov':'main'}
                except:
                    author_out[author] = {'formatted_name': formatted_name, 'wikidata_obj': {'head': {'vars': ['item', 'label']}, 'results': {'bindings': []}}}

                if len(author_out[author]['wikidata_obj']['results']['bindings']) == 0:
                    try:
                        a2 = search_query.format(auth_name=formatted_name)
                        res = execute_sparql_query(a2, max_retries=5)
                        #print("Fallback: ", res)
                        author_out[author]['wikidata_obj'] = res
                        author_out[author]['prov'] = 'fallback'
                    except:
                        pass

            else:
                author_out[author] = {'formatted_name': None, 'wikidata_obj': {'head': {'vars': ['item', 'label']}, 'results': {'bindings': []}}}

    print(len(author_out))
    print("Correctly formatted name:")
    print(len([a for a in author_out.keys() if author_out[a]['formatted_name'] is not None]))
    print("Found data:")
    print(len([a for a in author_out.keys() if len(author_out[a]['wikidata_obj']['results']['bindings']) > 0]))
    with outfile.open('w', encoding='utf-8') as json_out:
        json.dump(author_out, json_out, ensure_ascii=False, indent=4)



if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('infile', type=str)
    args.add_argument('outfile', type=str)
    parsedArgs = args.parse_args()

    main(Path(parsedArgs.infile), Path(parsedArgs.outfile))