'''
Uses wikidata uris from the URI query step to get advanced info about authors. Includes a step for disambiguating between authors with multiple
URI results
Inputs: JSON author uri file
Outputs: JSON author info file
Author: Craig Messner
'''

import json
from pathlib import Path
import argparse
import editdistance
import requests
from wikibaseintegrator.wbi_datatype import Url
from wikibaseintegrator.wbi_core import ItemEngine

from qwikidata.linked_data_interface import get_entity_dict_from_api

def main(infile, outfile):
    author_info_dict = {}
    with infile.open(encoding='utf-8') as authorsIn:
        author_json = json.load(authorsIn)

        for author in author_json:
            bindings = author_json[author]['wikidata_obj']['results']['bindings']
            uri = None
            info_dict = {}

            if len(bindings) > 1: #handle multiple possible objects. Currently just picking the 0 indexed exact comparison.
                ed_d = [editdistance.eval(author_json[author]['formatted_name'], potential['label']['value']) for potential in bindings]
                exact_matches = [index for index, val in enumerate(ed_d) if val == 0]
                if len(exact_matches) > 0:
                    uri = bindings[exact_matches[0]]['item']['value']


            elif len(bindings) == 1: #one possible result
                uri = bindings[0]['item']['value']

            if uri is not None:
                id = uri.split('/')[-1]
                api_uri = 'https://www.wikidata.org/wiki/Special:EntityData/'+id+'.json'
                response = requests.get(api_uri)
                if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type',''):
                    final_dict = {}
                    item_json = response.json()
                    print(author)
                    info_dict['citizenship'] = item_json['entities'][id]['claims'].get('P27') #citizenship
                    info_dict['birth'] = item_json['entities'][id]['claims'].get('P19') #place of birth
                    info_dict['death'] = item_json['entities'][id]['claims'].get('P20') #place of death
                    info_dict['burial'] = item_json['entities'][id]['claims'].get('P119') #place of burial
                    info_dict['residence'] = item_json['entities'][id]['claims'].get('P551')

                    for info_key, info_val in info_dict.items():
                        if info_val is not None:
                            try:
                                info_id = info_val[0]['mainsnak']['datavalue']['value']['id']
                                info_uri = 'https://www.wikidata.org/wiki/Special:EntityData/' + info_id + '.json'
                                info_response = requests.get(info_uri)
                                info_json = info_response.json()
                                final_dict[info_key] = {'id': info_id,
                                                        'label': info_json['entities'][info_id]['labels']['en']['value']}
                            except KeyError:
                                final_dict[info_key] = None

                            if final_dict[info_key]:
                                physical_location = info_json['entities'][info_id]['claims'].get('P625')
                                if physical_location:
                                    try:
                                        long = physical_location[0]['mainsnak']['datavalue']['value']['longitude']
                                        lat = physical_location[0]['mainsnak']['datavalue']['value']['longitude']
                                        final_dict[info_key]['coord'] = [lat, long]
                                    except KeyError:
                                        final_dict[info_key]['coord'] = None



                            print(final_dict[info_key])


                        else:
                            final_dict[info_key] = None

                    author_info_dict[author] = final_dict

            else:
                author_info_dict[author] = None

        with outfile.open('w', encoding='utf-8') as json_out:
            json.dump(author_info_dict, json_out, ensure_ascii=False, indent=4)





if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('infile', type=str)
    args.add_argument('outfile', type=str)
    parsedArgs = args.parse_args()

    main(Path(parsedArgs.infile), Path(parsedArgs.outfile))