def taskforce_from_guide(
    json_taskforce = '../data/taskforce.json',
    dir_wikidot: str = DIR_WIKIDOT,
) -> list[dict]:
    list_taskforce_dict = load_json(json_taskforce)
    list_sample = []
    list_address = []
    for dict_taskforce in list_taskforce_dict:
        name: str = dict_taskforce['name']
        if '特遣队' in name:
            name_split = re.sub(r'.*特遣队', '', name)
        elif 'MTF' in name:
            name_split = re.sub(r'mtf-?', '', name, flags=re.I)
        pattern = '[-\s]?'.join(name_split)
        pattern = r'(?:特遣队)?(?:机动.*队)?(?:[ms]tf)?[-\s]?' + pattern + r'[-\s]?'
        list_quote = [r'\(\)', r'（）', r'“”',r'‘’', r'\"\"', r'\'\'', r'「」']
        list_pattern_quote = [get_pattern_quote(i)+'?' for i in list_quote]
        pattern += ''.join(list_pattern_quote)
        pattern = re.compile(pattern, re.I)
        list_address = []
        for i in ['object_utilized', 'object_contained', 'action_report']:
            list_address += dict_taskforce[i]
        for address in list_address:
            html_path = dir_wikidot + address + '.html'
            text = get_page_text(html_path)
            list_sentence = split_sentence(text)
            for sentence in list_sentence:
                list_match = re.findall(pattern, sentence)
                if len(list_match) > 0:
                    sample = get_sample_dict(sentence, 'SCP基金会机动特遣队', list_match)
                    list_sample.append(sample)
    return list_sample