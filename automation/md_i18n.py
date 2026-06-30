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

    md_list: list[str] =   [technical, roadmap, readme, agent]
    # Get files in sub-folders (Only md)
    dirs: list[str] = os.listdir(f'{root_folder}')

    def get_files(folder: str):
        '''
            Auxiliar Function For Could
            use recursivity to iterates
            over all sub folders
        '''
        # Get Files From Root (Level 1) to Last Folder With md files (Level 5)
        for file_name in dirs:
            # Level 1
            if os.path.isdir(file_name):
                # Iterative Case: is Directory
                dirs_1 = os.listdir(file_name)
                if (not dirs.__contains__(dirs_1[0])):
                    dirs.__add__(dirs_1)
                for names_1 in dirs_1:
                    # Level 2
                    dirs_2 = os.listdir(names_1)
                    if (not dirs.__contains__(dirs_2[0])):
                        dirs.__add__(dirs_2)
                    for names_2 in dirs_2:
                        # Level 3
                        dirs_3 = os.listdir(names_2)
                        if (not dirs.__contains__(dirs_3[0])):
                            dirs.__add__(dirs_3)
                        for names_3 in dirs_3:
                            # Level 4
                            dirs_4 = os.listdir(names_3)
                            if (not dirs.__contains__(dirs_4[0])):
                                dirs.__add__(dirs_4)
                            for names_4 in dirs_4:
                                # Level 5
                                dirs_5 = os.listdir(names_4)
                                if (not dirs.__contains__(dirs_5[0])):
                                    dirs.__add__(dirs_5)    
                        
            elif (file_name.__contains__('.md') and (not md_list.__contains__(file_name))):
                # Only Add New Files: Base Case, is a file
                md_list.append(f'{folder}/{file_name}')
             
    # Add Translation for each content in respective file
    for language in lang_codes:
        for content in md_list:
            content.translation(language)