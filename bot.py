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
    """Inicia o navegador Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(20)  # Aumenta o tempo de espera implícito
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
        # Divide a mensagem em linhas para evitar problemas com mensagens muito longas
        linhas = mensagem.split('\n')
        
        # Lista de seletores para tentar encontrar o campo de texto
        input_selectors = [
            'div[data-testid="conversation-compose-box-input"]',
            'div[contenteditable="true"]',
            'div[title="Mensagem"]',
            'div[data-tab="10"]',
            'div[role="textbox"]',
            'footer div[contenteditable="true"]'
        ]
        
        campo_texto = None
        for selector in input_selectors:
            try:
                print(f"Tentando seletor: {selector}")
                campo_texto = driver.find_element(By.CSS_SELECTOR, selector)
                if campo_texto:
                    print(f"Campo de texto encontrado com seletor: {selector}")
                    break
            except:
                continue
        
        if not campo_texto:
            raise Exception("Não foi possível encontrar o campo de texto")
        
        # Clica no campo e espera um pouco
        campo_texto.click()
        time.sleep(1)
        
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

def obter_ultimas_mensagens(driver, num_mensagens=5):
    """Obtém as últimas mensagens do chat"""
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
        
        # Se encontrou mensagens, pega as últimas
        if mensagens:
            ultimas_msgs = mensagens[-num_mensagens:]
            resultado = []
            
            for msg in ultimas_msgs:
                try:
                    texto = msg.text.strip()
                    # Tenta pegar o timestamp do elemento pai
                    try:
                        pai = msg.find_element(By.XPATH, './ancestor::div[@data-pre-plain-text]')
                        data = pai.get_attribute('data-pre-plain-text')
                    except:
                        data = ""
                    
                    if texto:
                        print(f"Mensagem encontrada: {texto}")
                        resultado.append((texto, data))
                except:
                    continue
            
            return resultado
        
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
        
        # Dá um tempo extra para garantir que tudo carregou
        print("Aguardando mais alguns segundos para garantir que tudo carregou...")
        time.sleep(10)
        
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
        
        ultima_mensagem = ""
        print("Bot pronto para responder mensagens! Digite uma mensagem começando com 'GPT' no seu chat.")
        
        while True:
            try:
                # Obtém as últimas mensagens
                mensagens = obter_ultimas_mensagens(driver)
                
                # Processa cada mensagem
                for texto_msg, timestamp in mensagens:
                    # Verifica se é uma nova mensagem e começa com "GPT"
                    if texto_msg != ultima_mensagem and texto_msg.upper().startswith("GPT"):
                        pergunta = texto_msg[3:].strip()  # Remove "GPT" do início
                        print(f"Nova pergunta detectada: {pergunta}")
                        
                        # Obtém resposta do ChatGPT
                        print("Obtendo resposta do ChatGPT...")
                        resposta = obter_resposta_chatgpt(pergunta)
                        print(f"Resposta obtida: {resposta[:100]}...")
                        
                        # Envia a resposta
                        print("Enviando resposta...")
                        enviar_mensagem(driver, resposta)
                        print("Resposta enviada com sucesso!")
                        
                        ultima_mensagem = texto_msg
                        # Pequena pausa para evitar processamento duplicado
                        time.sleep(2)
                        break
                
                # Espera um pouco antes de verificar novamente
                time.sleep(1)
                
            except Exception as e:
                print(f"Erro ao processar mensagens: {str(e)}")
                time.sleep(5)
                
    except TimeoutException:
        print("Tempo excedido ao carregar o WhatsApp Web. Por favor, verifique sua conexão com a internet.")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
    finally:
        print("\nPressione Enter para fechar o bot...")
        try:
            input()
        except:
            pass
        print("Fechando o navegador...")
        driver.quit()
        print("Bot encerrado!")

if __name__ == "__main__":
    main()
