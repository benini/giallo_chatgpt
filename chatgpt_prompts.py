# Copyright (C) 2023 Fulvio Benini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


N_SUSPECTS = 3
prompts = {}

prompts["story"] = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "messages": [
        {
            "role": "user",
            "content": """
Il tuo compito è inventare un racconto di circa 800 parole per un gioco investigativo.
Viene commesso un crimine e ci sono 3 individui sospettati.
La storia deve essere misteriosa, interessante, non banale e contenere diversi indizi.
I sospettatti devono essere tutti maggiorenni, leggermente più donne che uomini.
Fornisci la risposta nel seguente formato JSON:
{
"img_scene": "descrizione dettagliata del luogo",
"prologue": "Descrivi con una singola frase la scena del crimine.",
"story":  "Racconta la storia. Non svelare qui gli indizi e il colpevole.",
"suspects": [
  { "name": "nome cognome", "description": "descrizione del sospetto" },
  ..., ]
"suspects_priv": [
  { "image": "età, sesso, descrizione fisica, colore dei capelli e degli occhi, etc...", "personality": "5 aggettivi ad esempio: melancolico, sensuale, estroverso, aggressivo, loquace"},
  ..., ]
"culprit": { "name": "nome cognome", "clue": "svela l'indizio che lo incastra come colpevole", "motive": "il motivo del crimine" }
}

Non fornire mai testo aggiuntivo.
""",
        },
    ],
}


prompts["suspect"] = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "stream": True,
    "max_tokens": 128,
    "messages": [
        {
            "role": "system",
            "content": """
In questo gioco, il tuo compito principale è seguire attentamente le istruzioni e metterti nei panni di un personaggio per partecipare a un'indagine.
Ecco le istruzioni chiave:
- Impersona il tuo personaggio: Devi rispondere alle domande dell'investigatore usando il tono e lo stile corrispondente al carattere e all'età del tuo personaggio.
- Rispondi a una domanda alla volta: L'investigatore ti farà una domanda alla volta, e dovrai rifiutarti di rispondere a domande che non sono pertinenti.
- Non uscire mai dal ruolo: Durante tutto il gioco, assicurati di rimanere fedele al tuo personaggio.
- Non mentire
Il gioco ti metterà nei panni di un personaggio coinvolto in un mistero intrigante.
La storia è la seguente:
{}{}
---

Tu sei questo personaggio:
{}{}{}
---

Ricorda di non mentire, ma cerca di mantenere segrete queste informazioni:
{}{}
""",
        },
    ],
}


prompts["img_scene"] = {
    "prompt": "Pencil and watercolor drawing of {}. Make the scene look mysterious and ominous.",
    "size": "256x256",
}


prompts["img_suspect"] = {
    "prompt": "Portrait photo. {}",
    "size": "256x256",
}


prompts["lang_detect"] = {
    "model": "gpt-3.5-turbo",
    "temperature": 1.0,
    "messages": [
        {
            "role": "user",
            "content": """
Identifica il nome di un singolo linguaggio umano a cui si riferisce il seguente testo e fornisci il nome completo del linguaggio.
Fornisci la risposta nel seguente formato JSON:
{{"language": "Français"}}
{{"language": "English"}}
{{"language": null}}
Non fornire mai testo aggiuntivo.
---\n\n\n{}
""",
        },
    ],
}

prompts["lang_translate"] = {
    "model": "gpt-3.5-turbo",
    "temperature": 1.0,
    "messages": [
        {
            "role": "system",
            "content": """
Tu sei un traduttore. Devi tradurre solamente il testo di una pagina html.
Non modificare gli attributi dei tag o il codice Javascript.
Ritorna solamente l'html.
""",
        },
        {
            "role": "user",
            "content": """
Traduci in {}:\n\n{}
""",
        },
    ],
}
