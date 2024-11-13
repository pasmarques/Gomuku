import xmlrpc.client  # Importa a biblioteca para comunicação com o servidor via XML-RPC
import threading  # Importa a biblioteca para trabalhar com threads
import time  # Importa a biblioteca para manipulação de tempo

def imprimir_tabuleiro(tabuleiro):
    # Limpa a tela para exibir o tabuleiro atualizado
    print("\n" * 50)
    # Exibe o cabeçalho das colunas (0 a 14)
    print("  " + " ".join(str(i) for i in range(15)))
    # Exibe cada linha do tabuleiro com o índice correspondente
    for i, linha in enumerate(tabuleiro):
        print(f"{i} " + " ".join(linha))
    print()

def obter_coordenadas():
    # Lê as coordenadas do jogador e valida a entrada
    try:
        x = int(input("Digite a linha (0-14): "))
        y = int(input("Digite a coluna (0-14): "))
        # Verifica se as coordenadas estão dentro dos limites válidos
        if 0 <= x < 15 and 0 <= y < 15:
            return x, y
        else:
            print("Coordenadas inválidas. Digite números entre 0 e 14.")
            return obter_coordenadas()  # Chama a função novamente para coordenadas válidas
    except ValueError:
        # Trata o caso de entrada não numérica
        print("Entrada inválida. Digite números.")
        return obter_coordenadas()

def atualizar_jogo(servidor, simbolo_jogador, evento_desconexao, lock):
    # Inicializa o estado anterior do jogo como None para comparação
    ultimo_estado = None
    # Loop para verificar atualizações enquanto o evento de desconexão não for acionado
    while not evento_desconexao.is_set():
        try:
            with lock:  # Garante acesso exclusivo à comunicação com o servidor
                tabuleiro = servidor.obter_tabuleiro()  # Obtém o estado atual do tabuleiro
                vez = servidor.obter_vez()  # Verifica de quem é a vez
                # Verifica mensagem de término do jogo
                mensagem_termino = servidor.obter_mensagem_termino()

            # Se houver mensagem de término, exibe o resultado e encerra a thread
            if mensagem_termino:
                print(f"Resultado final: {mensagem_termino}")
                evento_desconexao.set()
                break

            # Se houve alteração no tabuleiro ou na vez, exibe o estado atualizado
            if (tabuleiro, vez) != ultimo_estado:
                imprimir_tabuleiro(tabuleiro)
                if vez == simbolo_jogador:
                    print("Sua vez!")
                else:
                    print("Aguardando o oponente...")
                ultimo_estado = (tabuleiro, vez)

            time.sleep(2)  # Espera 2 segundos antes da próxima atualização
        except Exception as e:
            # Trata erros de comunicação com o servidor
            print(f"Erro de comunicação com o servidor: {e}")
            break

def main():
    # Evento para sinalizar quando o jogo deve ser encerrado
    evento_desconexao = threading.Event()
    try:
        # Conecta ao servidor na URL especificada
        servidor = xmlrpc.client.ServerProxy(
            "http://localhost:8000/", allow_none=True)
        # Escolhe o símbolo do jogador ('X' ou 'O')
        simbolo_jogador = input("Escolha seu símbolo ('X' ou 'O'): ").upper()

        # Valida a escolha do símbolo do jogador
        while simbolo_jogador not in ["X", "O"]:
            print("Símbolo inválido! Escolha 'X' ou 'O'.")
            simbolo_jogador = input(
                "Escolha seu símbolo ('X' ou 'O'): ").upper()

        # Solicita ao servidor para o jogador entrar no jogo com o símbolo escolhido
        resposta = servidor.entrar_jogo(simbolo_jogador)
        print(resposta)
        if "entrou" not in resposta:
            return  # Sai do jogo se a entrada não for bem-sucedida

        lock = threading.Lock()  # Lock para sincronizar o acesso ao servidor
        # Inicia uma thread para atualizar o jogo constantemente
        thread_atualizacao = threading.Thread(
            target=atualizar_jogo, args=(
                servidor, simbolo_jogador, evento_desconexao, lock), daemon=True
        )
        thread_atualizacao.start()

        # Loop principal do jogo
        while not evento_desconexao.is_set():
            with lock:
                vez = servidor.obter_vez()  # Verifica de quem é a vez

            # Se for a vez do jogador
            if vez == simbolo_jogador:
                with lock:
                    tabuleiro = servidor.obter_tabuleiro()  # Obtém o estado atual do tabuleiro
                imprimir_tabuleiro(tabuleiro)
                print("Sua vez!")

                # Solicita as coordenadas do movimento
                x, y = obter_coordenadas()
                with lock:
                    resultado = servidor.fazer_movimento(
                        simbolo_jogador, x, y)  # Faz o movimento no servidor

                print(resultado)  # Exibe o resultado do movimento

                # Se o jogo terminou (vitória ou empate), encerra o loop principal
                if "venceu" in resultado or "empate" in resultado:
                    evento_desconexao.set()
                    break

            time.sleep(2)  # Espera 2 segundos antes de checar a vez novamente

        # Solicita ao servidor para desconectar o jogador
        servidor.desconectar(simbolo_jogador)
    except KeyboardInterrupt:
        print("Encerrando o jogo...")
    except Exception as e:
        # Exibe erros de conexão com o servidor
        print(f"Erro na conexão com o servidor: {e}")
    finally:
        # Garante que o evento de desconexão seja acionado ao final
        evento_desconexao.set()

if __name__ == "__main__":
    main()  # Executa o programa principal