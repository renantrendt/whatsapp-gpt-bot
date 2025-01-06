import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configura o cliente OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def iniciar_navegador():
    """Inicia o navegador Chrome mantendo a sessão"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless=new')  # Modo headless novo
    options.add_argument('--disable-notifications')
    options.add_argument('--remote-debugging-port=9222')
    
    # Configurações específicas para ambiente cloud
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--blink-settings=imagesEnabled=true')
    options.add_argument('--start-maximized')
    
    try:
        # Em ambiente cloud, não usamos perfil local
        if os.getenv('RAILWAY_ENVIRONMENT'):
            driver = webdriver.Chrome(options=options)
        else:
            # Adiciona o diretório do usuário para manter a sessão em ambiente local
            user_data_dir = os.path.join(os.getcwd(), 'chrome_profile')
            options.add_argument(f'user-data-dir={user_data_dir}')
            options.add_argument('--profile-directory=WhatsApp')
            driver = webdriver.Chrome(options=options)
        
        driver.implicitly_wait(20)
        return driver
    except Exception as e:
        print(f"Erro ao iniciar o navegador: {str(e)}")
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            # Remove perfil apenas em ambiente local
            import shutil
            user_data_dir = os.path.join(os.getcwd(), 'chrome_profile')
            if os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir)
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(20)
        return driver

def esperar_elemento(driver, selector, by=By.CSS_SELECTOR, timeout=60):
    """Espera um elemento aparecer na página"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

def obter_resposta_chatgpt(pergunta):
    """Obtém uma resposta do ChatGPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": pergunta}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao obter resposta do ChatGPT: {str(e)}"

def enviar_mensagem(driver, mensagem):
    """Envia uma mensagem no WhatsApp"""
    try:
        # Lista de seletores específicos para o campo de mensagem do WhatsApp
        input_selectors = [
            'div[title="Digite uma mensagem"]',
            'div[data-testid="conversation-compose-box-input"]',
            'footer div[contenteditable="true"]',
            'div[contenteditable="true"][data-tab="10"]',
            'div[contenteditable="true"][title="Digite uma mensagem"]',
            'div[contenteditable="true"][data-lexical-editor="true"]'
        ]
        
        campo_texto = None
        for selector in input_selectors:
            try:
                print(f"Tentando seletor: {selector}")
                campo_texto = driver.find_element(By.CSS_SELECTOR, selector)
                if campo_texto and campo_texto.is_displayed():
                    print(f"Campo de texto encontrado com seletor: {selector}")
                    break
            except:
                continue
        
        if not campo_texto:
            raise Exception("Não foi possível encontrar o campo de texto")
        
        # Clica no campo e espera um pouco
        campo_texto.click()
        time.sleep(1)
        
        # Limpa o campo de texto antes de enviar a nova mensagem
        campo_texto.clear()
        time.sleep(0.5)
        
        # Divide a mensagem em linhas para enviar
        linhas = mensagem.split('\n')
        
        # Envia cada linha da mensagem
        for linha in linhas:
            # Envia a linha caractere por caractere
            for char in linha:
                campo_texto.send_keys(char)
                time.sleep(0.01)  # Pequena pausa entre caracteres
            
            # Pressiona Shift + Enter para nova linha, exceto na última linha
            if linha != linhas[-1]:
                campo_texto.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.1)
        
        # Envia a mensagem
        campo_texto.send_keys(Keys.ENTER)
        time.sleep(1)  # Pequena pausa para garantir que a mensagem foi enviada
        
    except Exception as e:
        print(f"Erro ao enviar mensagem: {str(e)}")
        raise e

def obter_ultimas_mensagens(driver, num_mensagens=1):
    """Obtém a última mensagem do chat"""
    try:
        # Lista de seletores para encontrar mensagens
        message_selectors = [
            'div.message-in span.selectable-text',
            'div[data-pre-plain-text] span.selectable-text',
            'div.copyable-text span.selectable-text',
            'div[role="row"] span.selectable-text'
        ]
        
        # Tenta cada seletor
        mensagens = []
        for selector in message_selectors:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    print(f"Mensagens encontradas com seletor: {selector}")
                    mensagens.extend(elementos)
            except:
                continue
        
        # Se encontrou mensagens, pega apenas a última
        if mensagens:
            ultima_msg = mensagens[-1]
            try:
                texto = ultima_msg.text.strip()
                # Tenta pegar o timestamp do elemento pai
                try:
                    pai = ultima_msg.find_element(By.XPATH, './ancestor::div[@data-pre-plain-text]')
                    data = pai.get_attribute('data-pre-plain-text')
                except:
                    data = ""
                
                if texto:
                    print(f"Última mensagem encontrada: {texto}")
                    return [(texto, data)]
            except:
                pass
        
        return []
    except Exception as e:
        print(f"Erro ao obter mensagens: {str(e)}")
        return []

def main():
    print("Iniciando o bot...")
    
    # Inicia o navegador
    driver = iniciar_navegador()
    print("Navegador iniciado com sucesso!")
    
    # Abre o WhatsApp Web
    driver.get("https://web.whatsapp.com")
    print("Por favor, escaneie o código QR do WhatsApp Web...")
    
    ultima_mensagem_respondida = None
    
    try:
        # Espera o WhatsApp Web carregar verificando diferentes elementos
        print("Aguardando o WhatsApp Web carregar...")
        
        # Tenta diferentes seletores para detectar quando o WhatsApp Web carregou
        selectors_to_try = [
            (By.CSS_SELECTOR, '[data-icon="menu"]'),
            (By.CSS_SELECTOR, 'div[role="textbox"]'),
            (By.XPATH, '//*[@id="side"]'),
            (By.CSS_SELECTOR, 'div[data-testid="chat-list"]'),
            (By.CSS_SELECTOR, 'div[data-testid="default-user"]'),
            (By.CSS_SELECTOR, 'div[data-testid="menu-bar"]'),
            (By.XPATH, '//div[@role="navigation"]')
        ]
        
        whatsapp_loaded = False
        for by, selector in selectors_to_try:
            try:
                esperar_elemento(driver, selector, by=by, timeout=20)
                whatsapp_loaded = True
                print(f"WhatsApp Web carregado! (detector: {selector})")
                break
            except:
                continue
        
        if not whatsapp_loaded:
            print("Não foi possível detectar o carregamento do WhatsApp Web.")
            return
        
        print("WhatsApp Web carregado com sucesso!")
        
        # Encontra o chat do usuário
        print("Procurando seu chat...")
        
        # Primeiro, garante que estamos na lista de chats
        try:
            botao_voltar = driver.find_element(By.CSS_SELECTOR, 'span[data-icon="back"]')
            botao_voltar.click()
            print("Voltando para a lista de chats...")
            time.sleep(2)
        except:
            print("Já estamos na lista de chats")
        
        # Tenta diferentes maneiras de encontrar o chat
        chat_selectors = [
            (By.XPATH, "//span[contains(text(), '+55 11 99492-0199')]"),
            (By.XPATH, "//div[contains(@title, '+55 11 99492-0199')]"),
            (By.XPATH, "//span[contains(text(), '(você)')]"),
            (By.CSS_SELECTOR, 'div[data-testid="cell-frame-title"]')
        ]
        
        chat_encontrado = False
        for by, selector in chat_selectors:
            try:
                print(f"Tentando encontrar chat com seletor: {selector}")
                chats = driver.find_elements(by, selector)
                for chat in chats:
                    try:
                        texto = chat.text
                        print(f"Chat encontrado: {texto}")
                        elemento_clicavel = chat
                        
                        # Tenta encontrar o elemento pai que pode ser clicado
                        for _ in range(5):
                            try:
                                elemento_clicavel.click()
                                chat_encontrado = True
                                print(f"Chat encontrado e selecionado! (usando {selector})")
                                time.sleep(2)  # Espera o chat carregar
                                break
                            except:
                                try:
                                    elemento_clicavel = elemento_clicavel.find_element(By.XPATH, '..')
                                except:
                                    break
                        
                        if chat_encontrado:
                            break
                    except:
                        continue
                
                if chat_encontrado:
                    break
            except Exception as e:
                print(f"Erro ao tentar seletor {selector}: {str(e)}")
                continue
        
        if not chat_encontrado:
            print("Chat não encontrado. Por favor, verifique se você está logado no WhatsApp Web.")
            return
        
        while True:
            try:
                # Obtém apenas a última mensagem
                mensagens = obter_ultimas_mensagens(driver, num_mensagens=1)
                
                if mensagens and mensagens[0][0] != ultima_mensagem_respondida:
                    mensagem = mensagens[0][0]
                    
                    # Verifica se a mensagem começa com "GPT"
                    if mensagem.lower().startswith('gpt'):
                        print(f"Nova pergunta recebida: {mensagem}")
                        resposta = obter_resposta_chatgpt(mensagem)
                        enviar_mensagem(driver, resposta)
                        ultima_mensagem_respondida = mensagem
                
                time.sleep(1)  # Espera 1 segundo antes de verificar novamente
                
            except Exception as e:
                print(f"Erro no loop principal: {str(e)}")
                time.sleep(5)  # Espera 5 segundos antes de tentar novamente
                
    except Exception as e:
        print(f"Erro: {str(e)}")
    finally:
        print("Encerrando o bot...")
        try:
            input()
        except:
            pass
        print("Fechando o navegador...")
        driver.quit()
        print("Bot encerrado!")

if __name__ == "__main__":
    main()
