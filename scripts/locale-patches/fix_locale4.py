files = {
    'fr': ('Invites', 'Déduplication'),
    'ru': ('Промпты', 'Дедупликация'),
    'zh-CN': ('提示词', '去重'),
    'ja': ('プロンプト', '重複排除'),
    'ar': ('المطالبات', 'إزالة التكرار'),
}

replacements = {
    'fr': ('Bibliothèque', 'Laboratoire de compétences'),
    'ru': ('Библиотека', 'Лаборатория навыков'),
    'zh-CN': ('库', '技能实验室'),
    'ja': ('ライブラリ', 'スキルラボ'),
    'ar': ('المكتبة', 'مختبر المهارات'),
}

for locale, (prompts, dedup) in files.items():
    path = f'interfaces/webui/src/locales/{locale}.json'
    with open(path, 'r') as f:
        content = f.read()
    
    lib, skill = replacements[locale]
    
    search = '"library": "' + lib + '", "skills_lab": "' + skill + '",'
    
    if search not in content:
        print(f'{locale}: NOT FOUND')
        continue
    
    new_text = '"library": "' + lib + '", "prompts": "' + prompts + '", "dedup": "' + dedup + '", "skills_lab": "' + skill + '",'
    
    content = content.replace(search, new_text)
    
    skills_key = '"skills_lab":' + skill + '"'
    idx = content.find(skills_key)
    comma_pos = content.find(',', idx)
    content = content[:comma_pos+1] + '} ' + content[comma_pos+1:]
    
    with open(path, 'w') as f:
        f.write(content)
    print(f'{locale}: Fixed')
