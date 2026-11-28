from search import search_prompt


def main():
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return
    
    print("Faça sua pergunta (digite 'sair' para encerrar):")

    while True:
        pergunta = input("\nPERGUNTA: ").strip()

        if pergunta.lower() == "sair":
            print("Até logo!")
            break

        if not pergunta:
            continue

        resposta = chain(pergunta)
        print(f"RESPOSTA: {resposta}")


if __name__ == "__main__":
    main()