import csv
import json
import requests
from bs4 import BeautifulSoup


# Pega todos 
def getCursosGradCvs():
    # Lista de Todos os Cursos
    url = "https://www.siga.ufrj.br/sira/repositorio-curriculo/80167CF7-3880-478C-8293-8E7D80CEDEBE.html"
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "html5lib")
    main_table = soup.find("table", class_="cellspacingTable")
    cursos= {}
    ultimo_curso = ""
    append_cursos = False

    # Para Cada 'chunk' de cursos
    for bodys in main_table.find_all("tbody"):

        # Curso atual é um braço de outro curso
        if bodys.attrs:
            append_cursos = True

        # Para Cada Linha da Tabela
        for curso in bodys.find_all("tr"):
            nome_curso = curso.find("b")
            curso_dict = {}

            # Texto atual não é um curso
            if not nome_curso.attrs:
                continue

            # Nome do Curso Atual
            nome_curso = nome_curso.text.strip()
            
            # Curriculos do Curso Atual
            curriculos_curso = curso.find_all("a")
            for curriculo in curriculos_curso:
                prepend = "javascript:Ementa('/sira/temas/zire/frameConsultas.jsp?mainPage=/"

                # Caso Não Tenha Link
                if not curriculo['href']:
                    continue

                # Filtra Link Para o Curriculo
                link = curriculo['href'].replace(prepend, "https://www.siga.ufrj.br/sira/").strip("')")
                curriculo_link = (curriculo.text, link)

                if "curriculos" in curso_dict:
                    curso_dict["curriculos"].append(curriculo_link)
                else:
                    curso_dict["curriculos"] = [curriculo_link]

            # Se o Curso Atual For Uma Vertente do Curso Anterior
            if append_cursos:
                ultimo_curso_dict = cursos[ultimo_curso]
                curso_dict["Nome"] = nome_curso
               
                if "vertentes" in ultimo_curso_dict:
                    ultimo_curso_dict["vertentes"].append(curso_dict)
                else:
                    ultimo_curso_dict["vertentes"] = [curso_dict]
            else:
                cursos[nome_curso] = curso_dict
                ultimo_curso = nome_curso

        # Próximo 'Chunk' não é mais uma vertente
        if append_cursos:
            append_cursos = False

    return cursos


def writeToFile(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
