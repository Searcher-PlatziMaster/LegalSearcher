from classifier import *
import os
from support import *
from text_filters import *

import requests
import json

def get_files(codes_folder, return_entries=False):
    codes_path = os.path.abspath(codes_folder)
    entries = os.listdir(codes_path)

    codes = []

    for entry in entries:

        entry_path = os.path.join(codes_folder, entry)
        with open(entry_path, 'r', encoding='utf-8') as f:
            text = f.readlines()
            
            f.close()
        
        for line in text:
            if line == '\n':
                text.remove(line)
            if line == ' \n':
                text.remove(line)
                
        codes.append(text)

    removal = codes[1][2]
    removal

    for code in codes:
        for line in code:
            if line == removal:
                code.remove(line)

    if return_entries == True: 
        return codes, entries
    else:
        return codes

def show_codes_content(codes, entries, hierarchy):
    main_list = []
    for entry, code in zip(entries, codes):
        print(entry, code[0])
        
        main_section = ""
        code_info = {'main' : None,
                    'n_sections': 0,
                    'sections': set(),
                    'last_section': None,
                    }

        sections_count = {
            'book': 0,
            'part' : 0,
            'headline': 0,
            'chapter': 0,
            'section': 0,
            'article' : 0
        }

        level = {
            'book': 6,
            'part' : 5,
            'headline': 4,
            'chapter': 3,
            'section': 2,
            'article' : 1
        }

        max_level = 0
        for line in code:
            hint = first_word(line).upper()
            hint = standarize(hint)
            if hint in hierarchy and hint != 'ARTICULO':
                reference = hierarchy[hint]
                code_info['last_section'] = reference

                if level[reference] > max_level:
                    code_info['main'] = reference
                    max_level = level[reference]

                # This will be done for sure
                code_info['n_sections'] += 1
                code_info['sections'].add(reference)

            if hint in hierarchy:
                reference = hierarchy[hint]
                sections_count[reference] += 1

                if reference == 'article':
                    sections_count[reference] += 1
                    
        main_list.append(code_info['main'])
        for key, value in code_info.items():
            print(key, ':', value)

        for key, value in sections_count.items():
            print(key, ':', value)

        print("\n-------------------------------\n")

def create_json_files(codes, entries, codes_id, show_difference=False):
    c = 1
    total = len(codes)
    pline = '\n----------------------'
    for entry, code in zip(entries, codes):
    
        code_id = codes_id[entry]
        code_info = {
            'id': code_id,
            'source_name': code[0],
        }
        print(f'LOADING: {c}/{total}', code[0])
        code.pop(0)
        text = code
        art_list = articles_info(code_info, text, debugging=False)
        
        if show_difference: print('File:', entry,'total lines = ', len(art_list))
        
        dot_text = split_text_in_lines(text, delimiter=".")
        if show_difference: print('File:', entry, 'Total elements by dot:', len(dot_text), )
        
        ndot_text = text_removals(dot_text)
        dcomma_text = split_text_in_lines(ndot_text, delimiter=";")
        if show_difference: print('File:', entry, 'Total elements by dot-comma:', len(dcomma_text), pline)
        
        dcomma_text = split_text_in_lines(ndot_text, delimiter="-")
        if show_difference: print('File:', entry, 'Total elements by dot-comma:', len(dcomma_text), pline)
        
        dcomma_text = split_text_in_lines(ndot_text, delimiter="°")
        if show_difference: print('File:', entry, 'Total elements by dot-comma:', len(dcomma_text), pline)
        
        embed_list = articles_info(code_info, dcomma_text, debugging=False)
        
        for embed, article in zip(embed_list, art_list):
            article['dot_comma_sep'] = embed['article']['content']
            
        levels = { 'book','part', 'headline', 'chapter', 'section', 'article' }
        json_list = format_articles(art_list, headers_dict=levels, debugging=False)
        
        dict_json = json.dumps(json_list, ensure_ascii=False)
        embedding_f = f'../ReadFiles/Embeddings/{code_id}-embedding.json'
        filepath = os.path.abspath(embedding_f)


        file = open(embedding_f, "w")
        file.write(dict_json)
        file.close()
        
        
        print('File created')
        print(' * - * * - * * - * * - * * - * * - * * - * * - * ')
        c = c + 1

def load_to_es_docker(codes_folder):
    codes_path = os.path.abspath(codes_folder)
    toLoad_entries = os.listdir(codes_path)
    e = 0
    total = len(toLoad_entries)
    for entry in toLoad_entries:
        log_info = {'id': None,
                'status': None,
                'error': None,
                'message': None,
                }
        e += 1
        entry_path = os.path.join(codes_folder, entry)
        
        with open(entry_path, 'r') as json_file:
            data = json.load(json_file)
            
            print(f'Uploading to Elastic Search {e}/{total}:', entry, '\n')
            a = 0
            for article in data:
                article.pop('dot_comma_sep', None)
                article['embedds'] = embeddings[article['id']]

                es_article_url = f"{main_url}/_doc/{article['id']}"
                request_response = requests.put(es_article_url, json=article)
            
                log_info = add_to_log(log_info, request_response, article)

                if log_info['status'][-1] != 200:
                    for key, value in log_info.items():
                        print(key, ':', value)
            print('Finished the upload of', entry, '\n')
            print(' * - * - * - * - * - * - * - * - * - * ')
            json_file.close()