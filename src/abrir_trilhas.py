"""Inicia o Trilhas RJ localmente e abre a interface no navegador."""
import webbrowser
from http.server import ThreadingHTTPServer

from planejar_trilha import Planejador


def main():
    with ThreadingHTTPServer(("127.0.0.1", 0), Planejador) as servidor:
        endereco = f"http://127.0.0.1:{servidor.server_port}/"
        print(f"Trilhas RJ está disponível em {endereco}", flush=True)
        print("Mantenha esta janela aberta enquanto usar o sistema.", flush=True)
        try:
            webbrowser.open(endereco)
        except webbrowser.Error:
            print("Abra o endereço acima no seu navegador.", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
