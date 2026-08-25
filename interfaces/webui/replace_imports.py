import os
import glob

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.ts') or file.endswith('.tsx'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                new_content = content.replace('@/core/api', '@/api')
                new_content = new_content.replace('@/core/providers', '@/providers')
                new_content = new_content.replace('@/core/store', '@/store')
                new_content = new_content.replace('@/features', '@/components/features')
                new_content = new_content.replace('../../../core/api', '../../api')
                new_content = new_content.replace('../../core/api', '../api')
                
                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")

if __name__ == '__main__':
    replace_in_files('/home/fatsio/AI/Ethan/interfaces/webui/src')
