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
    "model": "gpt-4-1106-preview",
    "temperature": 0.7,
    "response_format": { "type": "json_object" },
    "messages": [
        {
            "role": "user",
            "content": """
Il tuo compito è inventare un racconto di circa 800 parole per un gioco investigativo.
Viene commesso un crimine e ci sono 3 individui sospettati.
La storia deve essere misteriosa, interessante, non banale e contenere indizi nascosti.
I sospettatti devono essere tutti maggiorenni, leggermente più donne che uomini.
Crea un valido oggetto JSON seguendo questo schema:
{
"img_scene": "descrizione dettagliata del luogo",
"prologue": "Descrivi con una singola frase la scena del crimine.",
"story":  "Racconta la storia. Non svelare qui il colpevole.",
"suspects": [
  { "name": "nome cognome", "description": "descrizione del sospetto" },
  ..., ]
"suspects_priv": [
  { "image": "età, sesso, descrizione fisica, colore dei capelli e degli occhi, etc...", "personality": "5 aggettivi ad esempio: melancolico, sensuale, estroverso, aggressivo, loquace"},
  ..., ]
"culprit": { "name": "nome cognome", "clue": "svela l'indizio che lo incastra come colpevole", "motive": "il motivo del crimine" }
}

Evita qualunque testo oltre all oggetto JSON:
""",
        },
    ],
}


prompts["suspect"] = {
    "model": "gpt-4-1106-preview",
    "temperature": 1.0,
    "stream": True,
    "max_tokens": 256,
    "messages": [
        {
            "role": "system",
            "content": """
Il gioco ti metterà nei panni di un personaggio coinvolto in un mistero intrigante.
Il tuo compito è impersonare un personaggio di un gioco investigativo.
Devi rispondere alle domande dell'investigatore usando il tono e lo stile corrispondente al carattere e l'età del tuo personaggio.
L'investigatore deve farti una sola domanda alla volta, rifiutati anche di rispondere a domande che non sono pertinenti.
Non uscire mai dal ruolo.
La storia è la seguente:
{}{}
---

Tu sei:
{}.{}{}{}
---

Non mentire, ma cerca di mantenere segrete queste informazioni:
Il colpevole è {}.{}{}
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


prompts["tts"] = {
  "model": "tts-1",
  "voice": "onyx",
  "input": "{}"
}


prompts["lang_detect"] = {
    "model": "gpt-3.5-turbo-1106",
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
    "model": "gpt-3.5-turbo-1106",
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
