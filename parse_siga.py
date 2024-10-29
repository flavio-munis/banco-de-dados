import csv
import json
import requests
from bs4 import BeautifulSoup


output_base = 'siga2/'

def getLocalAddress(page_url):
    return page_url.replace("https://www.siga.ufrj.br/sira/repositorio-curriculo/", output_base)


def getFile(localAddress):

    with open(localAddress, 'r') as f:
        text = f.read()

    return text


# Pega todos 
def getCursosGradCvs():
    # Lista de Todos os Cursos
    local_url = f'{output_base}/80167CF7-3880-478C-8293-8E7D80CEDEBE.html'

    html_text = getFile(local_url)

    soup = BeautifulSoup(html_text, "html5lib")
    main_table = soup.find("table", class_="cellspacingTable")
    cursos= {}

    # Para Cada 'chunk' de cursos
    for bodys in main_table.find_all("tbody"):

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
                prepend = "javascript:Ementa('/sira/temas/zire/frameConsultas.jsp?mainPage=/repositorio-curriculo/"

                # Caso Não Tenha Link
                if not curriculo['href']:
                    continue

                # Filtra Link Para o Curriculo
                link = curriculo['href'].replace(prepend, output_base).strip("')")
                realLink = getCurriculumRealLink(link)
                curriculo_info = {"date": curriculo.text,
                                  "linkSiga": realLink}

                if "curriculos" in curso_dict:
                    curso_dict["curriculos"].append(curriculo_info)
                else:
                    curso_dict["curriculos"] = [curriculo_info]

            if not "curriculos" in curso_dict:
                continue

            curso_dict['nome'] = nome_curso

            if not "cursos" in cursos:
                cursos["cursos"] = [curso_dict]
            else:
                cursos["cursos"].append(curso_dict)

    return cursos



def getCurriculumRealLink(currLink):

    html_text = getFile(getLocalAddress(currLink))
    soup = BeautifulSoup(html_text, "html5lib")
    realLink = soup.find(id="frameDynamic").get('src')

    realLink = f'https://www.siga.ufrj.br/sira/repositorio-curriculo/{realLink}'

    return realLink


def parseInfoTable(info_table):

    info = {}
    isData = False
    lastHeader = ""

    # Campo de Informações
    for row in info_table.find_all('tr'):

        # Informações
        for data in row.find_all('td', class_='identacao1'):

            headerName = data.find('strong')

            if isData:
                info[lastHeader] = data.text
                isData = False
                continue

            if headerName:
                isData = True
                lastHeader = headerName.text.strip(": ")
                continue

    return info


def getPeriodosInfo(tables):

    periodos = {}

    for table in tables:

        # Check if Current Table is Not Empty
        table = table.find("table", class_="cellspacingTable")

        if not table:
            continue

        # Check if Current Table has a Title
        title = table.find('tr', class_= "tableTitle")

        if not title:
            continue

        # Check if the Title Contains the Word "Período"
        if not "Período" in title.td.b.text:
            continue

        title = title.td.b.text.strip(" ")

        if title == "Obrigatórias s/ Período":
            n_periodo = 0
        else:
            n_periodo = int(title.split("º Período")[0])

        info_table = table.find_all('tbody')[1]
        info_rows = info_table.find_all('tr', recursive=False)[1:-1]

        if not info_rows:
            continue

        periodo = {'materias': []}

        for row in info_rows:
            materia = getMateriaInfo(row)

            if not materia:
                continue

            periodo['materias'].append(materia)

        periodos[n_periodo] = periodo

    return periodos


def parsePrerequisites(pre_requisito):

    # If empty or just whitespace/newlines, return empty string
    if not pre_requisito or pre_requisito.strip() == '\n\t':
        return ''

    # Remove newlines and tabs
    cleaned = pre_requisito.strip()
    
    # Split by comma to get individual prerequisites
    prereqs = [p.strip() for p in cleaned.split(',')]
    
    # Keep only codes that have (P)
    final_prereqs = []
    for prereq in prereqs:
        # Check if this prerequisite has (P)
        if '(P)' in prereq:
            # Get the code part (everything before any equals sign or space)
            code = prereq.split('=')[0].split()[0]
            # Remove (P) from the code
            code = code.replace('(P)', '').strip()
            final_prereqs.append(code)

    return final_prereqs


def getMateriaInfo(row):

    materia = {}
    prepend = "javascript:Ementa(\'../"
    start = 0

    info_list = row.find_all('td')

    # In Case There's a Row With Wrong Format 
    if len(info_list) < 5:
        return {}

    # Checks if Current Materia Has a Link Attributed to It
    linkMateria = info_list[start].find('a')
    
    # If There's a Link
    if linkMateria:
        linkMateria = linkMateria['href']
        linkMateria = linkMateria.split(prepend)[1].strip(')')
        linkMateria = f'https://www.siga.ufrj.br/sira/repositorio-curriculo/{linkMateria}'
    
        html_text = getFile(getLocalAddress(linkMateria))
        soup = BeautifulSoup(html_text, "html5lib")
    
        sibling = soup.find('tr', class_= "tableTitleBlue")
        materia_descr = sibling.find_next_sibling().td.text

        codigoMateria = info_list[start].a.text
        start += 1

    # If There's Not A Link
    else:
        linkMateria = ''
        materia_descr = ''
        codigoMateria = info_list[start].text

    nomeMateria = info_list[start].text
    start += 1

    creditos = float(info_list[start].text)
    start += 1

    horas = float(info_list[start].text)
    start += 1

    horas += float(info_list[start].text)
    start += 1

    horas += float(info_list[start].text)
    start += 1

    pre_requisito = info_list[start].text
    pre_requisito = parsePrerequisites(pre_requisito)

    materia["link"] = linkMateria
    materia["creditos"] = int(creditos)
    materia["codigo"] = codigoMateria
    materia["nome"] = nomeMateria
    materia["descricao"] = materia_descr
    materia["horas"] = int(horas)
    materia["pre_requisito"] = pre_requisito

    return materia


def getCurriculoInfo(curriculo_link):

    html_text = getFile(curriculo_link)
    soup = BeautifulSoup(html_text, "html5lib")

    main_table = soup.find('tbody')
    tables = main_table.find_all('tr', recursive=False)

    # Primeira tabela sempre é a de informação
    info_table = tables[0].find('tbody')
    infos_dict = parseInfoTable(info_table)

    periodos_info = getPeriodosInfo(tables[1:])



def getCursosInfo(cursos):

    for curso in cursos['cursos']:

        print(curso["nome"])

        for curriculo in curso["curriculos"]:
            html_text = getFile(getLocalAddress(curriculo["linkSiga"]))
            soup = BeautifulSoup(html_text, "html5lib")

            print(f'{curriculo["date"]}...')

            main_table = soup.find('tbody')
            tables = main_table.find_all('tr')

            # Primeira tabela sempre é a de informação
            info_table = tables[0].find('tbody')
            infos_dict = parseInfoTable(info_table)

            if not "Código" in curso:
                curso["Código"] = infos_dict["Código"]

            periodos_info = getPeriodosInfo(tables[1:])
            curriculo["periodos"] = periodos_info

    return cursos



def writeToFile(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def readFile(path):
    with open(path, "r", encoding='utf-8') as f:
        data = json.load(f)

    return data
