import http.client
import json
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import unicodedata
import time

from os import system
import xml.etree.ElementTree as ET
import ssl
import websockets

from tts import TTS

not_quit = True
intent_before = ""
products_retrived = []

intents_list = ["ask_help", "show_products", "open_website", "scroll_up", "scroll_down", "select_product_by_position", "add_to_cart", "add_to_favorites", "show_cart", "show_favorites", "remove_cart", "remove_favorites", "go_back", "show_more", "finalize_order", "main_page", "order_products"]

driver = None

# Função para abrir o site (exemplo, IKEA) usando o Selenium
def open_website():
    """
    Função que usa o Selenium para abrir o site do IKEA e tentar clicar no botão de aceitação de cookies.
    """
    global driver
    website = "https://www.ikea.com/pt/pt/"  # URL do site para abrir

    try:
        # Verifica se o driver já está ativo ou precisa ser reiniciado
        if driver is None or not is_driver_alive():
            # Caminho do driver do Selenium (atualize conforme necessário)
            # service = Service("C:\\Users\\Usuario\\Downloads\\chromedriver-win64\\chromedriver.exe")  # Atualize para o caminho correto
            service = Service("C:\\Users\\rober\\Downloads\\chromedriver-win64\\chromedriver.exe")  # Atualize para o caminho correto
            driver = webdriver.Chrome(service=service)
        
        # Abre o site
        driver.get(website)
        driver.maximize_window()  # Maximiza a janela do navegador

        # Espera e tenta clicar no botão de aceitação de cookies
        try:
            wait = WebDriverWait(driver, 10)
            cookie_button = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
        except Exception:
            print("Não foi possível encontrar o botão de aceitação de cookies.")
        
        print(f"Abrindo o site do IKEA Portugal...")

    except Exception as e:
        print(f"Erro ao abrir o site: {str(e)}")

def remove_accents(input_str):
    if input_str is not None:
        # Transforma em formato Unicode Normalizado e remove caracteres acentuados
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return None

def show_product(category, tts):

    #remove acentos qualquer tipo de acento
    category2 = remove_accents(category)

    global driver

    if driver is None:
        print("Driver não foi inicializado.")
        return
      
    if not category:
        tts(text="Não consegui entender a categoria que gostaria de procurar.")
        return []

    try:
            
        print("A iniciar pedido:")
        tts(f"A procurar por {category} no site da IKEA Portugal")
            
        # Conexão com a API do IKEA
        conn = http.client.HTTPSConnection("ikea-api.p.rapidapi.com")
        # Headers para autenticação
        headers = {
            'x-rapidapi-key': "f6ac7694f0mshad1a1e112b29308p1def65jsn84a5131e4970",
            'x-rapidapi-host': "ikea-api.p.rapidapi.com"
        }

        # Endpoint da API com o termo de busca
        endpoint = f"/keywordSearch?keyword={category2}&countryCode=pt&languageCode=pt"

        # Faz a requisição à API
        conn.request("GET", endpoint, headers=headers)

        print(f"Requisição GET para {endpoint}")
        

        res = conn.getresponse()
        data = res.read()
        products = json.loads(data.decode("utf-8"))  # Decodifica a resposta JSON

        products_retrived.clear()
        
        for product in products:
                products_retrived.append(product)

            # Verifica se há produtos na resposta
        if not products:
            tts(f"Não encontrei produtos na categoria '{category}'.")
            return []

        # Prepara a lista de produtos
        product_list = "\n".join([
            f"- {item['name']} (Preço: {item['price']['currentPrice']} {item['price']['currency']})"
            for item in products[:5]  # Mostra os 5 primeiros produtos
        ])

        tts(f"Aqui estão alguns produtos da categoria '{category}'!")

    except Exception as e:
        # Tratamento de erros
        tts("Desculpe, houve um problema ao procurar os produtos. Tente novamente mais tarde.")
        print(f"Erro na integração com a API do IKEA: {e}")

    try:
        print("Buscando no site da IKEA com Selenium...")

        driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")

        time.sleep(2)

        # Localiza o campo de busca
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-field__input"))
            )            
        search_box.send_keys(Keys.CONTROL + "a")  # Seleciona todo o texto
        search_box.send_keys(Keys.BACKSPACE)  # Apaga o texto selecionado
        search_box.send_keys(category2)

        # Aciona o botão de busca
        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-box__searchbutton"))  # Ajuste conforme o ID correto
        )
        search_button.click()

    except Exception as e:
            tts("Houve um problema ao realizar a busca no site. Tente novamente mais tarde.")
            print(f"Erro no Selenium: {e}")

    return []


def is_driver_alive() -> bool:
    """
    Verifica se o driver do Selenium ainda está ativo.
    """
    try:
        driver.title  # Verifica se o driver ainda tem acesso à página
        return True
    except:
        close_driver()  # Fecha o driver se não estiver mais ativo
        return False

def close_driver():
    """
    Fecha o driver se ele estiver inicializado.
    """
    global driver
    if driver:
        try:
            driver.quit()  # Fecha o driver do Selenium
        except Exception:
            pass  # Ignora exceções durante o fechamento
        driver = None  # Define o driver como None após fechá-lo

def scroll_down():
    """
    Rola a página para baixo usando o Selenium.
    """
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Rola a página suavemente para baixo (500px)
        driver.execute_script("window.scrollBy({top: 500, behavior: 'smooth'});")  # Ajuste o valor conforme necessário
        print("A página foi rolada para baixo.")
    
    except Exception as e:
        print(f"Houve um problema ao rolar a página: {e}")

def scroll_up():
    """
    Rola a página para cima usando o Selenium.
    """
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Rola a página suavemente para cima (500px)
        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")  # Ajuste o valor conforme necessário
        print("A página foi rolada para cima.")
    
    except Exception as e:
        print(f"Houve um problema ao rolar a página: {e}")

def select_product_by_positions(position, tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
            # Verifica se a posição foi fornecida e é válida
    if not position:
        tts("Desculpe, não entendi a posição do produto que você quer.")
        return []

    try:
        # Converte a posição para inteiro
        position = int(position) - 1  # Subtrai 1 para ajustar ao índice da lista (começa em 0)
        print(f"Selecionando produto na posição {position + 1}...")
        
        product_retrived = products_retrived[position]
        print(product_retrived)
        driver.get(product_retrived['url'])
        tts(
            f"Selecionei o produto na posição {position + 1}, {products_retrived['name']}!."
        )
    except ValueError:
        tts("Por favor, informe um número válido para a posição.")
    except Exception as e:
        tts("Houve um problema ao selecionar o produto. Tente novamente mais tarde.")
        print(f"Erro ao selecionar produto: {e}")

    return []
    
def open_cart(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        driver.get("https://www.ikea.com/pt/pt/shoppingcart/")
        print("O carrinho foi aberto.")
        tts("O carrinho foi aberto.")
    except Exception as e:
        tts("Não foi possível abrir o carrinho.")
        print(f"Erro ao abrir o carrinho: {e}")

    return []

def open_favourites(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        driver.get("https://www.ikea.com/pt/pt/favourites/")

        wait = WebDriverWait(driver, 15)
        select_list_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ListThumbnail_container__tCqlx"))
        )
        driver.execute_script("arguments[0].click();", select_list_button)

        print("Os favoritos foram abertos.")
        tts("Os favoritos foram abertos.")
    except Exception as e:
        tts("Não foi possível abrir os favoritos.")
        print(f"Erro ao abrir os favoritos: {e}")

    return []

def add_to_cart(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
    try:
        # Localiza o botão de adicionar ao carrinho
        wait = WebDriverWait(driver, 15)
        add_to_cart_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--emphasised.pip-btn--fluid"))
        )

        print("A clicar no botão de adicionar ao carrinho...")
        driver.execute_script("arguments[0].click();", add_to_cart_button)
        
        wait = WebDriverWait(driver, 15)
        close_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rec-modal-header__close"))
        )

        print("A clicar no botão de fechar...")
        driver.execute_script("arguments[0].click();", close_button)
        tts("O produto foi adicionado ao carrinho.")

    except Exception as e:
        tts("Não foi possível adicionar o produto ao carrinho.")
        print(f"Erro ao adicionar ao carrinho: {e}")
    
    return []

def add_to_favorites(tts):
    
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Localiza o botão de adicionar aos favoritos
        wait = WebDriverWait(driver, 15)
        add_to_favorites_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--small.pip-btn--icon-primary-inverse.pip-favourite-button"))
        )

        print("A clicar no botão de adicionar aos favoritos...")
        driver.execute_script("arguments[0].click();", add_to_favorites_button)
        tts("O produto foi adicionado aos favoritos.")
    except Exception as e:
        tts("Não foi possível adicionar o produto aos favoritos.")
        print(f"Erro ao adicionar aos favoritos: {e}")

    return []

def remove_from_cart(position, tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
    try:
        # Localiza o botão de remover do carrinho
        wait = WebDriverWait(driver, 15)
        buttons = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//button[contains(@aria-label, 'Remover produto')]"))
        )

        print(f"Botões de remover do carrinho: {len(buttons)}")

        if 0 < int(position) <= len(buttons):
            print(f"A clicar no botão {position} de remover do carrinho...")
            buttons[int(position) - 1].click()
            tts("O produto foi removido do carrinho.")
        else:
            tts("A posição fornecida não é válida.")
            print("Erro: Posição fora do intervalo.")

    except Exception as e:
        tts("Não foi possível remover o produto do carrinho.")
        print(f"Erro ao remover do carrinho: {e}")
    
    return []

def remove_from_favorites(position, tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        wait = WebDriverWait(driver, 15)
        
        # Encontra todos os botões de remover dos favoritos
        buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "button[aria-label^='Remover']"))
        )

        if 0 < int(position) <= len(buttons):
            print(f"A clicar no botão {position} de remover dos favoritos...")
            buttons[int(position) - 1].click()
            tts("O produto foi removido dos favoritos.")
        else:
            tts("A posição fornecida não é válida.")
            print("Erro: Posição fora do intervalo.")
    except Exception as e:
        tts("Não foi possível remover o produto dos favoritos.")
        print(f"Erro ao remover dos favoritos: {e}")
    
    return []

def go_back(tts):
    """
    Função para voltar à página anterior no navegador.
    """
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        tts("O navegador não foi iniciado. Por favor, tente novamente.")
        return

    try:
        # Comando do Selenium para voltar à página anterior
        driver.back()
        print("Página anterior.")
        tts("Página anterior.")
    except Exception as e:
        tts("Não foi possível voltar à página anterior.")
        print(f"Erro ao voltar à página anterior: {e}")
    
    return []

def show_more(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
    try:

        # Localiza o botão "Mostrar mais"
        wait = WebDriverWait(driver, 15)
        show_more_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a [aria-label='Mostrar mais produtos']"))
        )

        print("A clicar no botão de mostrar mais...")
        driver.execute_script("arguments[0].click();", show_more_button)
        tts("Mostrando mais produtos.")
    except Exception as e:
        tts("Não foi possível mostrar mais produtos.")
        print(f"Erro ao mostrar mais produtos: {e}")
    
    return []

# FALTA AQUI O FINALIZAR A COMPRA

def finalize_order(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Localiza o botão de finalizar a compra
        wait = WebDriverWait(driver, 15)
        checkout_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'cart-ingka-jumbo-btn--emphasised')]"))
        )

        print("A clicar no botão de finalizar a compra...")
        driver.execute_script("arguments[0].click();", checkout_button)


        print("A clicar no botão de confirmar a finalização da compra...")
        wait = WebDriverWait(driver, 15)
        confirm_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'cart-ingka-btn--emphasised')]"))
        )

        print("A clicar no botão de confirmar a compra...")
        driver.execute_script("arguments[0].click();", confirm_button)

        tts("A finalizar a compra.")
    except Exception as e:
        tts("Não foi possível finalizar a compra.")
        print(f"Erro ao finalizar a compra: {e}")
    
    return []

def main_page(tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        tts("O navegador não foi iniciado. Por favor, tente novamente.")
        return

    try:
        # Define a URL da página inicial
        homepage_url = "https://www.ikea.com/pt/pt/"  # Substitua pela URL desejada

        # Navega para a página inicial
        driver.get(homepage_url)
        print("Voltando à página inicial.")
        tts("Voltando à página inicial do site.")
    except Exception as e:
        tts("Não foi possível voltar à página inicial.")
        print(f"Erro ao voltar à página inicial: {e}")
    
    return []


def order_products(criterio, tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
    try:

        print(f"Ordenando produtos por '{criterio}'...")
        wait = WebDriverWait(driver, 15)
        # Usando XPath com texto
        # all_filters_button = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Todos os filtros')]"))
        # )

        # Alternativa usando as classes
        all_filters_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Todos os filtros']]"))
        )

        print("A clicar no botão de todos os filtros...")
        driver.execute_script("arguments[0].click();", all_filters_button)


        # Localiza o botão de ordenar produtos
        wait = WebDriverWait(driver, 15)
        sort_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'plp-accordion__heading plp-accordion-item-header plp-accordion-item-header--large')]"))
        )

        print("A clicar no botão de ordenar produtos...")
        driver.execute_script("arguments[0].click();", sort_button)


        # Ajusta o critério para "Preço: mais elevado ao mais baixo" ou "Preço: mais baixo ao mais elevado"
        if criterio == "mais elevado ao mais baixo" or criterio == "do mais elevado ao mais baixo":
            criterio = "Preço: mais elevado ao mais baixo" 
        if criterio == "mais baixo ao mais elevado" or criterio == "do mais baixo ao mais elevado":
            criterio = "Preço: mais baixo ao mais elevado"
            
        # Localiza a opção de ordenação desejada

        if criterio == "Preço: mais elevado ao mais baixo":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[3]'))
            )
        
        if criterio == "Preço: mais baixo ao mais elevado":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[2]'))
            )

        if criterio == "Mais Recente":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[4]'))
            )
        
        if criterio == "Mais Populares":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[7]'))
            )

        if criterio == "Largura":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[8]'))
            )
        
        if criterio == "Altura":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[9]'))
            )

        if criterio == "Comprimento":
            sort_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="SEC_sort"]/div/div/fieldset/label[10]'))
            )
            

        print(f"A clicar na opção de ordenação por '{criterio}'...")
        driver.execute_script("arguments[0].click();", sort_option)


        print("A clicar no botão de ver!")

        ver_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="content"]/div/div[1]/div[1]/div[3]/div/div[3]/button[1]'))
        )

        driver.execute_script("arguments[0].click();", ver_button)

        tts(f"Os produtos foram ordenados por '{criterio}'.")

    except Exception as e:
        tts("Não foi possível ordenar os produtos.")
        print(f"Erro ao ordenar produtos: {e}")

def ask_help(tts):
    try:
        # Respostas diretas e simplificadas para o usuário
        help_messages = {
            'open_website': "Para abrir o site, diga 'Abre o site' ou 'Vamos às compras'.",
            'show_products': "Você pode me dizer 'Quero ver cadeiras' ou 'Mostra-me sofás' para ver os produtos.",
            'add_to_cart': "Para adicionar um produto ao carrinho, diga 'Adiciona o produto ao carrinho'.",
            'add_to_favorites': "Para salvar um produto nos favoritos, diga 'Adiciona aos favoritos'.",
            'show_cart': "Para ver seu carrinho, diga 'Mostrar-me o carrinho' ou 'Quero ver o meu carrinho'.",
            'remove_cart': "Se quiser remover algo do carrinho, diga 'Remove o produto número 1 do carrinho'.",
            'remove_favorites': "Para remover um item dos favoritos, diga 'Remove o produto número 1 dos favoritos'.",
            'go_back': "Para voltar à página anterior, diga 'Volta para trás'.",
            'main_page': "Para voltar à página inicial, diga 'Voltar à página inicial'.",
            'order_products': "Você pode ordenar os produtos por preço ou por popularidade, por exemplo, 'Ordena por preço', entre outros.",
            'scroll_up': "Para subir a página, diga 'Suba' ou 'Sobe para cima'.",
            'scroll_down': "Para descer a página, diga 'Desça' ou 'Desce para baixo'.",
            'show_more': "Para ver mais opções, diga 'Quero ver mais'.",
            'finalize_order': "Quando quiser finalizar a compra, diga 'Finaliza a compra' ou 'Procede para o checkout' dentro do carrinho."
        }

        # Escolhe uma mensagem aleatória ou a mais relevante
        message = "Aqui estão algumas coisas que você pode fazer:"

        for key in help_messages:
            message += f"\n- {help_messages[key]}"

        # Envia a mensagem
        tts(message)

    except Exception as e:
        # Se houver algum erro, exibe uma mensagem genérica
        tts("Desculpe, houve um erro ao tentar fornecer ajuda.")
        print(f"Erro ao fornecer ajuda: {e}")

    
async def message_handler(message, tts):
    # Processa a mensagem e extrai o intent
    message = process_message(message)
    print(f"Message: {message}")
    
    if message == "OK":
        return "OK"
    elif  message["intent"]["name"] in intents_list:
        intent = message["intent"]["name"]
        confidence = message["intent"]["confidence"]
        print(f"Intent: {intent} com confiança: {confidence}")
        if message["intent"]["confidence"] < 0.7:
            tts("Por favor repita o comando!")

        # Verifica o intent e executa a ação correspondente
        elif intent == "open_website":
            # Se o intent for "open_website", chama a função para abrir o site
            print("Abrindo o site...")
            tts("A abrir o site da IKEA PORTUGAL")
            open_website()

        elif intent == "show_products":
            # Aqui você pode adicionar lógica para mostrar produtos, etc.
            category = message['entities'][0]['value']
            print(f"Mostrando produtos de {category} ...")
            # Chame a função que exibe produtos aqui, por exemplo
            show_product(category, tts)

        elif intent == "scroll_down":
            # Se o intent for "scroll_up", chama a função para rolar para cima
            print("A descer a pagina")
            tts("A descer a página")
            scroll_down()

        elif intent == "scroll_up":
            # Se o intent for "scroll_up", chama a função para rolar para cima
            print("A subir a pagina")
            tts("A subir a página")
            scroll_up()

        elif intent == "select_product_by_position":
            position = message['entities'][0]['value']
            print(f"A selecionar o producto na posição {position}..")
            select_product_by_positions(position, tts)
        
        elif intent == "show_cart":
            print("A abrir ao carrinho...")
            open_cart(tts)

        elif intent == "show_favorites":
            print("A abrir os favoritos...")
            open_favourites(tts)

        elif intent == "add_to_cart":
            print("A adicionar ao carrinho...")
            add_to_cart(tts)
        
        elif intent == "add_to_favorites":
            print("A adicionar aos favoritos...")
            add_to_favorites(tts)

        elif intent == "remove_cart":
            print("A remover produto do carrinho...")
            position = message['entities'][0]['value']
            remove_from_cart(position, tts)

        elif intent == "remove_favorites":
            print("A remover produto dos favoritos...")
            position = message['entities'][0]['value']
            remove_from_favorites(position,tts)
        
        elif intent == "go_back":
            print("A voltar para trás")
            go_back(tts)

        elif intent == "show_more":
            print("A mostrar mais produtos")
            show_more(tts)

        elif intent == "finalize_order":
            print("A finalizar a encomenda")
            finalize_order(tts)

        elif intent == "main_page":
            print("Voltar à Página Inicial")
            main_page(tts)

        elif intent == "order_products":
            print("Ordenar Produtos")
            criterio = message['entities'][0]['value']
            order_products(criterio, tts)
        elif intent == "ask_help":
            print ("Ajuda")
            ask_help(tts)
        
        # Adicione outros intents conforme necessário, como scroll, add_to_cart, etc.
        
        else:
            print(f"Intent não reconhecido: {intent}")
            tts("Por favor repita o comando!")
    else:
        print(f"Intent não reconhecido: {intent}")
        tts("Por favor repita o comando!")

def process_message(message):
    if message == "OK":
        return "OK"
    else:
        json_command = ET.fromstring(message).find(".//command").text
        command = json.loads(json_command)["nlu"]
        command = json.loads(command)
        print(f"Command received: {command['text']}")
        return command

async def main():
    tts = TTS(FusionAdd="https://127.0.0.1:8000/IM/USER1/APPSHEECH").sendToVoice
    mmi_client_out_add = "wss://127.0.0.1:8005/IM/USER1/APP"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(mmi_client_out_add, ssl=ssl_context) as websocket:

        print("Connected to MMI Client")

        while not_quit: 
            try:
                msg = await websocket.recv()
                print(f"Received message: {msg}")
                await message_handler(message=msg, tts=tts)
            except Exception as e:
                tts("Por Favor repita o comando!")
                print(f"Error: {e}")
        
        print("Closing connection")
        await websocket.close()
        print("Connection closed")
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())
