import json

files = {
    'fr': ('Invites', 'Déduplication'),
    'ru': ('Промпты', 'Дедупликация'),
    'zh-CN': ('提示词', '去重'),
    'ja': ('プロンプト', '重複排除'),
    'ar': ('المطالبات', 'إزالة التكرار'),
}

# Values to replace for each locale
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
    
    # Find the library key and append prompts + dedup before skills_lab line
    # We search for: "library": "Bibliothèque", "skills_lab": "Laboratoire de compétences",
    # and replace with: "library": "Bibliothèque", "prompts": "Invites", "dedup": "Déduplication", "skills_lab": "Laboratoire de compétences",
    
    # Split the content at the navigation object
    # Find: "library": "Bibliothèque", "skills_lab": "Laboratoire de compétences",
    marker = '\\"library\\": \\"' + lib + '\\\", \\"skills_lab\\": \\"' + skill + '\\\",'
    # Actually let me just use Python string with raw content
    search_marker = '\\"library\\": \\"' + lib + '\\\", \\"skills_lab\\": \\"' + skill + '\\\",'
    
    print(f'{locale}: searching for {search_marker[:60]}...')
    if search_marker not in content:
        print(f'  NOT FOUND - skipping {locale}')
        continue
    
    # Create the new text to insert
    new_text = '\\"library\\": \\"' + lib + '\\\", \\"prompts\\": \\"' + prompts + '\\\", \\"dedup\\": \\"' + dedup + '\\\", \\"skills_lab\\": \\"' + skill + '\\\",'
    
    content = content.replace(search_marker, new_text)
    
    with open(path, 'w') as f:
        f.write(content)
    print(f'  Fixed {locale}.json')
