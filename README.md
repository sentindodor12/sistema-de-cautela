# ENC MAT 1ª CIA — Render

## Arquivos
- `app.py`: servidor Flask e API de cautelas.
- `templates/index.html`: tela inicial.
- `templates/dashboard.html`: painel principal.
- `static/1cia.png`: emblema.
- `cautelas.json`: dados iniciais importados do arquivo enviado.
- `requirements.txt` e `Procfile`: configuração de execução no Render.

## Publicar no Render
1. Extraia este ZIP.
2. Envie o conteúdo da pasta para um repositório GitHub.
3. No Render, escolha **New + → Web Service** e conecte o repositório.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Clique em **Create Web Service**.

O arquivo `render.yaml` também está incluído para configuração como Blueprint.

## Importante sobre os dados
O serviço usa `cautelas.json` como armazenamento. No Render, o disco do serviço pode ser efêmero; alterações feitas no site podem ser perdidas em novo deploy/reinício. Para manter os dados, configure um Persistent Disk pago montado no serviço e ajuste o caminho de `cautelas.json` para esse disco, ou migre para um banco de dados persistente (por exemplo PostgreSQL).

O JSON original contém dados pessoais, telefone e imagens de assinaturas. Confirme que você tem autorização para publicar esses dados e não deixe o sistema público sem autenticação se os registros forem restritos. O código original não implementa login.
