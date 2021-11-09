'''
Queries the metadata file in order to get unique word counts of included docs. by pub. year and their associated basic metadata. -w is a flag.
If enabled copies word data directly to the created JSON words file, if not (by default) includes directory path to word TSV instead
Arguments: infile outfile data_file_directory -s startyear -e endyear -w
Inputs: Metadata file
Outputs: JSON
Author: Craig Messner
'''
import argparse
import csv
from pathlib import Path
import json
from collections import defaultdict




#some imprints are expressed as ranges. just for now at least return the lower bound date
#also handle "estimate" and "unparsed" tags
def parse_imprint_year(year):
    if len(year) == 4 and year.isnumeric():
        return int(year)
    elif '-' in year and 'estimate' not in year and 'unparsed' not in year:
        range = year.split('-')
        return int(sorted(range)[0])
    else:
        return None

def check_in_range(year, begin, end):
    if year is None:
        return False

    elif year in range(begin, end+1):
        return True
    else:
        return False


def tsv_to_dict(tsv):
    tsv_word_reader = csv.reader(tsv, delimiter='\t', quotechar=None)
    return {line[0]: int(line[1]) for line in tsv_word_reader}


def main(infile, outfile, data_dir, start, end, words_flag):
    author_dict = defaultdict(list)
    with infile.open(encoding='utf-8') as metadataIn:
        metadata_reader = csv.DictReader(metadataIn, delimiter=',', quotechar='"')
        for line in metadata_reader:
            parsed_year = parse_imprint_year(line['imprintdate'])
            if check_in_range(parsed_year, start , end):
                data_file = data_dir.joinpath(line['htid'] + '.tsv')
                if words_flag:
                    try:
                        with data_file.open(encoding='utf-8') as wordDataIn:
                            word_data = tsv_to_dict(wordDataIn)
                    except FileNotFoundError:
                        word_data = None
                        print(data_file)
                else:
                    word_data = str(data_file)

                author_dict[line['author']].append({'htid': line['htid'], 'title': line['title'], 'date': parsed_year, 'words': word_data})


    with outfile.open('w', encoding='utf-8') as json_out:
        json.dump(author_dict, json_out, ensure_ascii=False, indent=4)





if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('infile', type=str)
    args.add_argument('outfile', type=str)
    args.add_argument('data_dir', type=str)
    args.add_argument('--start','-s', type=int, default=0) #arbitrary large and small numbers bigger than range
    args.add_argument('--end','-e', type=int, default=3000)
    args.add_argument('--words', '-w', type=bool, default=False)
    parsedArgs = args.parse_args()

    main(Path(parsedArgs.infile), Path(parsedArgs.outfile), Path(parsedArgs.data_dir), parsedArgs.start, parsedArgs.end, parsedArgs.words)
