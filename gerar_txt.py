import os

# Nome do arquivo de saída consolidado
arquivo_saida = "codigo_fonte_api.txt"

# Extensões ou arquivos que queremos incluir
arquivos_alvo = ["main.py", "models.py", "schemas.py", "database.py", "requirements.txt", "Procfile", "runtime.txt"]

print("📦 Gerando o arquivo de texto com o código fonte completo...")

with open(arquivo_saida, "w", encoding="utf-8") as f_out:
    f_out.write("==================================================\n")
    f_out.write("     PROJETO API AGENDACARE - CODIGO FONTE\n")
    f_out.write("==================================================\n\n")
    
    arquivos_encontrados = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            if file in arquivos_alvo or file.endswith(".py"):
                caminho_completo = os.path.join(root, file)
                
                # Ignora pastas virtuais ou de ambiente
                if ".venv" in caminho_completo or "__pycache__" in caminho_completo or file == "gerar_txt.py" or file == arquivo_saida:
                    continue
                
                arquivos_encontrados += 1
                f_out.write(f"\n\n{'='*50}\n")
                f_out.write(f"ARQUIVO: {caminho_completo}\n")
                f_out.write(f"{'='*50}\n\n")
                
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f_in:
                        f_out.write(f_in.read())
                except Exception as e:
                    f_out.write(f"[Erro ao ler o arquivo: {e}]\n")

print(f"✨ Sucesso! {arquivos_encontrados} arquivos foram consolidados no arquivo '{arquivo_saida}'.")