# Importa o servidor XML-RPC para comunicação remota
from xmlrpc.server import SimpleXMLRPCServer
import threading  # Importa threading para gerenciar bloqueios de acesso simultâneo aos recursos do servidor

# Define a classe do servidor Gomoku, que gerencia o estado do jogo e permite a interação dos jogadores
class ServidorGomoku:
    def __init__(self):
        # Inicializa o servidor e configura o jogo como pronto para começar
        self.resetar_jogo()

    # Método para um jogador entrar no jogo
    def entrar_jogo(self, simbolo_jogador):
        with self.lock:  # Usa um bloqueio para evitar condições de corrida
            # Verifica se o símbolo escolhido é válido
            if simbolo_jogador not in ["X", "O"]:
                return "Símbolo inválido! Escolha 'X' ou 'O'."

            # Verifica se o jogo está cheio e se o símbolo já não foi escolhido por outro jogador
            if len(self.jogadores) < 2 and simbolo_jogador not in self.jogadores:
                self.jogadores[simbolo_jogador] = True  # Adiciona o jogador
                # Quando dois jogadores entram, o jogo é marcado como iniciado
                if len(self.jogadores) == 2:
                    self.jogo_iniciado = True
                return f"Jogador {simbolo_jogador} entrou no jogo!"
            return "Jogo cheio ou símbolo já escolhido!"

    # Método para fazer um movimento no tabuleiro
    def fazer_movimento(self, simbolo_jogador, x, y):
        with self.lock:  # Usa um bloqueio para sincronizar o acesso
            # Verifica se o jogo foi iniciado
            if not self.jogo_iniciado:
                return "Jogo não está pronto!"

            # Verifica se é a vez do jogador atual
            if simbolo_jogador != self.vez_atual:
                return "Não é sua vez, aguarde o oponente!"

            # Verifica se a posição escolhida está vazia (representada por '.')
            if self.tabuleiro[x][y] == ".":
                # Atualiza a posição no tabuleiro com o símbolo do jogador
                self.tabuleiro[x][y] = simbolo_jogador
                # Checa se o movimento levou à vitória
                if self.verificar_vitoria(simbolo_jogador):
                    self.finalizar_jogo(f"Jogador {simbolo_jogador} venceu!")
                    return self.mensagem_termino

                # Checa se o tabuleiro está cheio e o jogo terminou em empate
                if all(self.tabuleiro[i][j] != "." for i in range(15) for j in range(15)):
                    self.finalizar_jogo("O jogo terminou em empate!")
                    return self.mensagem_termino

                # Alterna a vez entre os jogadores
                self.vez_atual = "O" if self.vez_atual == "X" else "X"
                return "Movimento feito com sucesso"
            else:
                return "Movimento inválido! Posição já ocupada."

    # Método para verificar se um jogador venceu
    def verificar_vitoria(self, simbolo_jogador):
        # Verifica o tabuleiro inteiro para identificar uma sequência de 5 símbolos consecutivos
        for i in range(15):
            for j in range(15):
                # Verifica linhas, colunas e diagonais para uma linha de 5 símbolos consecutivos
                if (self.verificar_linha(i, j, 1, 0, simbolo_jogador) or
                    self.verificar_linha(i, j, 0, 1, simbolo_jogador) or
                    self.verificar_linha(i, j, 1, 1, simbolo_jogador) or
                        self.verificar_linha(i, j, 1, -1, simbolo_jogador)):
                    return True
        return False

    # Verifica uma linha de símbolos consecutivos na direção especificada
    def verificar_linha(self, x, y, dx, dy, simbolo_jogador):
        contagem = 0
        for i in range(5):  # Verifica 5 posições consecutivas
            nx, ny = x + i * dx, y + i * dy  # Calcula a posição na direção especificada
            # Verifica se a posição está dentro do tabuleiro e contém o símbolo do jogador
            if 0 <= nx < 15 and 0 <= ny < 15 and self.tabuleiro[nx][ny] == simbolo_jogador:
                contagem += 1
            else:
                break
        return contagem == 5  # Retorna True se houver 5 símbolos consecutivos

    # Método para obter o estado atual do tabuleiro
    def obter_tabuleiro(self):
        return self.tabuleiro

    # Método para obter qual é o jogador da vez
    def obter_vez(self):
        return self.vez_atual

    # Método para obter a mensagem de término do jogo
    def obter_mensagem_termino(self):
        return self.mensagem_termino

    # Método para desconectar um jogador do jogo
    def desconectar(self, simbolo_jogador):
        with self.lock:  # Bloqueio para evitar alterações simultâneas
            # Verifica se o jogador está na partida e remove-o se estiver
            if simbolo_jogador in self.jogadores:
                del self.jogadores[simbolo_jogador]
                # Se não houver jogadores restantes, o jogo é reiniciado
                if len(self.jogadores) == 0:
                    self.resetar_jogo()
                return "Jogador desconectado."
            return "Jogador não encontrado."

    # Método para reiniciar o jogo
    def resetar_jogo(self):
        # Configura o tabuleiro vazio e reinicia os atributos do jogo
        self.tabuleiro = [["." for _ in range(15)] for _ in range(15)]
        self.jogadores = {}
        self.vez_atual = "X"
        self.jogo_iniciado = False
        self.mensagem_termino = None
        self.lock = threading.Lock()  # Cria um bloqueio para gerenciar acesso concorrente

    # Método para finalizar o jogo e definir a mensagem de término
    def finalizar_jogo(self, mensagem):
        self.mensagem_termino = mensagem
        self.jogo_iniciado = False  # Define que o jogo não está mais em andamento

# Função para iniciar o servidor XML-RPC
def iniciar_servidor():
    # Cria o servidor XML-RPC na porta 8000, permitindo que métodos sejam chamados remotamente
    with SimpleXMLRPCServer(("localhost", 8000), allow_none=True) as servidor:
        # Registra uma instância do servidor Gomoku
        servidor.register_instance(ServidorGomoku())
        # Mensagem indicando que o servidor está em execução
        print("Servidor Gomoku está rodando...")
        try:
            servidor.serve_forever()  # Mantém o servidor rodando até que seja interrompido
        except KeyboardInterrupt:
            # Mensagem de encerramento ao interromper o servidor
            print("Servidor encerrado.")

# Executa o servidor se o script for iniciado diretamente
if __name__ == "__main__":
    iniciar_servidor()
