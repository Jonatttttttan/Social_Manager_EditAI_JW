# EditAI Videos JW v0.9.3 — Transições

Na aba **Editar um vídeo**, escolha um efeito em **Transições entre os cortes** e a duração (0,2–2,0 s). As transições são aplicadas entre os trechos preservados após os cortes, não nos intervalos removidos.

Efeitos: Nenhuma (padrão, comportamento anterior), Dissolver, Fade para preto, Deslizar. O áudio utiliza `acrossfade` para evitar cortes bruscos. A duração total diminui pela sobreposição de cada junção.

**Limitações:** não há transição quando sobra apenas um trecho. Um trecho menor que a duração escolhida gera erro claro; reduza a duração ou revise os cortes. A opção de transições foi adicionada à edição individual, não à edição em lote. A exportação com transições requer recodificação e pode ser mais lenta.

**Segurança:** a validação de licença continua no mesmo lugar, antes da edição. Esta versão não modifica o endereço do servidor de licenças.

**Teste no Windows:** instale dependências, execute `main.py`, analise um vídeo com pelo menos dois trechos preservados, escolha cada efeito e exporte; verifique imagem, áudio e duração. Recompile PyInstaller e Inno Setup somente depois dos testes.
