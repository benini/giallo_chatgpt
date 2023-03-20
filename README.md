# Giallo ChatGPT

Un gioco di investigazione dove il giocatore deve risolvere un crimine creato dall'AI.
Creato per testare le potenzialità delle nuove AI:
- Traduzione automatica delle pagine web in diverse lingue.
La pagina viene scritta in una sola lingua e l'AI la traduce automaticamente,
potenzialmente in 100 lingue diverse, la prima volta che viene richiesta da un utente.
La risposta viene salvata nella cache in modo che le richieste successive in quella lingua
non richiedono una nuova traduzione e, se la pagina viene modificata dal developer,
è sufficiente cancellare la cache per _"aggiornare"_ tutte le altre lingue.
Il vantaggio principale è che l'AI è in grado di comprendere la struttura html e tradurre solamente i testi, lasciando invariati codici e struttura.
- Originalità. Quanto sono diverse le storie generate usando sempre lo stesso prompt?
Quanto bassa si può impostare la temperatura rispetto allo 0.7 di default?
- Personalità, è possibile renderla meno _fredda_? Quanto è efficace e credibile l'AI nell'impersonare i sospetti che hanno personalità differenti?
- Immagini. Sfruttiamo le capacità di programmazione di chatGPT e gli chiediamo di generare i prompt di DALL-E necessari a produrre le immagini corrispondenti alle caratteristiche dei sospetti.
- Prompt in italiano. Si trovano molti video di esperimenti con chatGPT, ma tutti in inglese.
Usare dei prompt in italiano influenza l'output? Meglio, peggio o uguale?


## Scena 1
{Immagine della centrale e dell'investigatore.}
Un crimine, 4 sospetti.
Il tuo infallibile fiuto ti dice che il colpevole è uno di loro.
Interrogali e cerca le incongruenze, ma attenzione puoi fare solo 3 per ogni sospetto.
Al termine dell'interrogatorio richiama il colpevole e fallo confessare.
-- pulsante Inizia --


## Scena 2
{Immagine del luogo del crimine, create con DALL-E. Anche il prompt
viene generato automaticamente da chatGPT usando la storia come input}
Racconta (ed in futuro LEGGI) la storia del crimine creata da ChatGPT
-- pulsante Interrogatorio --

```python
class Crimine:
def __init__:
- self.storia = genera_storia
- self.personaggi = estrai_personaggi(self.storia)
def genera_storia:
- usiamo ChatGPT per generare la storia.
- il prompt non è facile, deve inventare una storia non banale, inventare i 5 personaggi, e l'incongruenza del colpevole.
def estrai_personaggi:
- dalla storia generata bisogna in qualche modo estrarre la descrizione dei sospetti e sapere chi è il colpevole.
  return [ Personaggio(descrizione, [incongruenze]) ]

```


## Scene 3,4,5,6
{Immagine del personaggio. Anche qui il prompt per DALL-E viene creato da chatGPT in base alla descrizione che lui stesso ha creato.}
Descrizione del personaggio
Chat dove l'investigatore può fare 3 domande. Viene chiesto a chatGPT di interpretare il personaggio e di fornire le risposte. Il colpevole deve avere una contraddizione che viene svelata solo se l'investigatore fa le domande giuste.
-- pulsante sospetto successivo --

```python
def genera_img_personaggio:
- usiamo DALL-E per generare l'immagine del sospetto

class Personaggio:
- self.descrizione
- self.contraddizioni
- self.immagine
def get_chatGPT_prompt:
- ritorna il prompt necessario affinchè ChatGPT interpreti il personaggio.
- La difficoltà è dargli una personalità.
```

## Scena Finale
{Immagini di tutti i personaggi}
{Per ogni personaggio riassunto? dell'interrogatorio}
-- scegli il colpevole --
Chat con una sola domanda
svela il colpevole e la contraddizione

## Riepilogo
- Viene svelato il colpevole, rivelazione della contraddizione.
- Congratulazioni se è stato smascherato.
- Riepilogo della storia, dei personaggi incluse le immagini e l'interrogatorio.

## Run
The app uses the Flask framework.
1. Create a new virtual environment:

   ```bash
   $ python -m venv venv
   $ . venv/bin/activate
   ```

2. Install the requirements:

   ```bash
   $ pip install -r requirements.txt
   ```

3. Add the [OPENAI API key](https://beta.openai.com/account/api-keys) to the `.env` file.
   ```ini
   OPENAI_API_KEY=your_key
   ```

8. Run the app:

   ```bash
   $ flask run
   ```

The app should now be available at [http://localhost:5000](http://localhost:5000)
