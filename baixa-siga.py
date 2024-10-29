import json
import requests
import os
from bs4 import BeautifulSoup

output_base = 'siga2/'


def savePage(page_text, page_url):

    page_local_path = page_url.replace("https://www.siga.ufrj.br/sira/repositorio-curriculo/", output_base)
    #page_name= page_local_path.split("/")[-1]
    
    print(f'Saving {page_local_path}...')

    with open(page_local_path, "w") as f:
        f.write(page_text)


def pageAlreadyExists(page_url):
    return os.path.exists(getLocalAddress(page_url))


def getLocalAddress(page_url):
    return page_url.replace("https://www.siga.ufrj.br/sira/repositorio-curriculo/", output_base)


def getFile(localAddress):

    with open(localAddress, 'r') as f:
        text = f.read()

    return text

def downloadGraduacao():

    url = "https://www.siga.ufrj.br/sira/repositorio-curriculo/80167CF7-3880-478C-8293-8E7D80CEDEBE.html"
    
    if pageAlreadyExists(url):
        html_text = getFile(getLocalAddress(url))
    else:
        html_text = requests.get(url).text
        savePage(html_text, url)

    soup = BeautifulSoup(html_text, "html5lib")
    links = soup.find_all('a')
    prependCurso = "javascript:Ementa('/sira/temas/zire/frameConsultas.jsp?mainPage=/"
    prependMateria = "javascript:Ementa('../"


    for link in links:
        linkConsulta = link['href'].replace(prependCurso, "https://www.siga.ufrj.br/sira/").strip("')")

        if not linkConsulta:
            continue

        if pageAlreadyExists(linkConsulta):
            html_text = getFile(getLocalAddress(linkConsulta))
        else:
            html_text = requests.get(linkConsulta).text
            savePage(html_text, linkConsulta)

        page = BeautifulSoup(html_text, "html5lib")
        src = page.find_all('frame')[1]['src']
        linkPage = f'https://www.siga.ufrj.br/sira/repositorio-curriculo/{src}'

        if not pageAlreadyExists(linkPage):
            html_text = requests.get(linkPage).text
            savePage(html_text, linkPage)
        else:
            localAddress = getLocalAddress(linkPage)
            html_text = getFile(localAddress)
            print(f'File in {localAddress}')

        curso = BeautifulSoup(html_text, "html5lib")
        materias = curso.find_all('a', class_= "linkNormal")

        for materia in materias:
            
            linkMateria = materia['href'].replace(prependMateria, "https://www.siga.ufrj.br/sira/repositorio-curriculo/").strip(")")
            
            if not pageAlreadyExists(linkMateria):
                materia_text = requests.get(linkMateria).text
                savePage(materia_text, linkMateria)
