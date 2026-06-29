#!/usr/bin/python3
# Translate all the Markdown in the folder and sub-folders to language
root_folder: str = '/workspaces/hanger/'
md_list: list[str] = []
lang_codes: list[str] =     [
                                'es', 'fr', 'de',
                                'ja', 'zh', 'uk',
                                'ru', 'it', 'pt'
                            ]
class Documents:
    '''
        Representation of reduced content from
        a document for don't read each time need
        the content for could write it.
    '''
    def __init__(self, file_path: str, first_line: int, last_line: int):
        # Only Save Content for Data Encapsulation to protect files
        self.content: str = ''
        
        with open(file_path, 'r') as doc:
            for line in range(first_line, last_line + 1):
                self.content += doc.readline()
            doc.close()
        
        self.doc_path: str = file_path

    def translation(self, code: str):
        '''
            Write Translation To Language code
            in file
        '''
        with open(self.doc_path, 'a') as translator:
            translated: str = self.content.replace('[EN]', '')
            translator.write(f'# [{code}] {translated}')
            translator.close()
            del translated

if __name__ == '__main__':
    import os

    os.system(f'cd {root_folder}')
    
    technical = Documents(f'{root_folder}/TECHNICAL_ROADMAP.md', 3, 98)

    roadmap = Documents(f'{root_folder}/ROADMAP.md', 1, 5)

    readme = Documents(f'{root_folder}/README.md', 3, 44)

    agent = Documents(f'{root_folder}/AGENTS.md', 1, 40)

    md_list =   [technical, roadmap, readme, agent]
    # Get files in sub-folders
    # Add Translation for each content in respective file
    for language in lang_codes:
        for content in md_list:
            content.translation(language)