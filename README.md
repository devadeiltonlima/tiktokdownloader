# 🎥 TikTok Downloader - Baixa aí sem marca d'água! 🚀

Fala meu consagrado! 👋

Esse projetinho aqui é pra quem tá cansado daquela marca d'água chata do TikTok dançando na tela. O esquema é simples: você manda o link, a gente devolve o vídeo limpinho ou só o áudio, se preferir. Tudo na faixa, sem enrolação. 😉

## 🤔 Qual é a mágica? (Como funciona por baixo dos panos)

O sistema é todo feito em **Python** com **Flask**, mas a gente não guarda nada no servidor pra não pesar a firma. O fluxo é vapt-vupt:

1.  **Você cola o link:** O usuário joga a URL do vídeo do TikTok lá no campo.
2.  **A gente corre atrás:** O backend recebe esse link e faz uma "ligação" (requisição) pra API do **TikWM**. É ela que tem o mapa da mina pra pegar o vídeo original sem a marca d'água.
3.  **Download Turbo:** O vídeo é baixado temporariamente numa pasta local (só de passagem, tá ligado?).
4.  **Entrega:**
    *   **Vídeo:** O sistema te manda o arquivo `.mp4` na qualidade máxima que achar.
    *   **Áudio:** Se você quiser só o som, a gente usa uma ferramenta chamada `moviepy` pra arrancar o áudio do vídeo e te entrega um `.mp3` estalando.
5.  **Faxina:** Depois que você baixa, o sistema passa a vassoura e apaga os arquivos temporários pra não ficar ocupando espaço à toa.

## ✨ O que dá pra fazer?

*   **Baixar Vídeo HD:** Pega o vídeo na melhor qualidade disponível, sem aquela logo flutuante.
*   **Extrair Áudio:** Curtiu só a música ou o áudio viral? Dá pra baixar só o MP3.
*   **Barra de Progresso:** Tem uma barrinha estilosa que te avisa passo a passo o que tá rolando (validando, baixando, finalizando...), pra você não ficar ansioso achando que travou.
*   **Nome do Arquivo:** O arquivo já vem com o nome certinho do vídeo, pra você não se perder na sua pasta de Downloads.

---

É isso aí! Simples, direto e funcional. Só colar, baixar e ser feliz. 😎🇧🇷
Feito por: @devadeiltonlima