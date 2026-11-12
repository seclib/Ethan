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
    
    search = '\\"library\\": \\"' + lib + '\\\", \\"skills_lab\\": \\"' + skill + '\\\",'
    
    if search not in content:
        print(f'{locale}: NOT FOUND')
        continue
    
    new_search = '\\"library\\": \\"' + lib + '\\\", \\"prompts\\": \\"' + prompts + '\\\", \\"dedup\\": \\"' + dedup + '\\\", \\"skills_lab\\": \\"' + skill + '\\\",'
    
    content = content.replace(search, new_search)
    
    # Now close the navigation object: find skills_lab key and add } after its comma
    # The text is: "skills_lab": "value",  - we need: "skills_lab": "value",
    # then add } before the 
  "actions"  or the ", that follows
    skills_pos = content.find('\\"skills_lab\\"', content)
    # Find the comma after skills_lab
    comma_pos = content.find(',', skills_pos)
    # The text after is ",  or ",  - we need to add } before that
    # Find the closing quote after the comma
    after_comma = content[comma_pos+1:comma_pos+5]
    
    # Replace: \"skills_lab\": \"value\",\n  "actions"
    # With:      \"skills_lab\": \"value\",\n  }
    old_tail = content[comma_pos:comma_pos+40]
    print(f'{locale}: tail after comma: {repr(old_tail[:40])}')
    
    # Insert } after the comma (before the newline and space)
    content = content[:comma_pos+1] + '} ' + content[comma_pos+1:]
    
    with open(path, 'w') as f:
        f.write(content)
    print(f'{locale}: Fixed')
