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


from openai_helper import AI
from chatgpt_prompts import prompts, N_SUSPECTS

import base64
from copy import deepcopy
from datetime import datetime
import json
import random
import secrets
import uuid
import flask


# AI.set_cache("redis://localhost:6379")
# AI.set_cache("dynamodb.giallo_chatgpt", endpoint_url="http://localhost:8000", aws_access_key_id='dummy', aws_secret_access_key='dummy')
# AI.set_cache("dynamodb.giallo_chatgpt")

suspects_interrogation = {}

N_QUESTIONS = 3
MAX_QUESTION_CHARS = 200
default_language = "Italiano"

app = flask.Flask(__name__)
app.secret_key = secrets.token_hex(32)

def valid_session(nr):
    crime_id = flask.session.get("crime_id")
    language = flask.session.get("language")
    session_id = flask.session.get("session_id")
    if not crime_id or not language or not session_id or not (nr is None or 0 < nr <= N_SUSPECTS):
        return (None, None, None)
    return crime_id, language, session_id

def lang_detect(language_name):
    detect = AI.send_message(prompts["lang_detect"], messages__content=language_name)
    return json.loads(detect).get("language")

def lang_translate(text, language):
    return AI.send_message(prompts["lang_translate"], messages__content=[language, text])


@app.route("/")
def index():
    language = flask.request.args.get("lang")
    if language and 2 <= len(language) <= 30:
        language = lang_detect(language)
    if not language:
        language = default_language

    # A random crime_id is generated once a day.
    # crime_id = generate_crime_id(datetime.now().strftime("%Y%m%d"))
    crime_id = random.choice(crime_pool(10))
    flask.session["crime_id"] = crime_id
    flask.session["language"] = language
    session_id = str(uuid.uuid4())
    flask.session["session_id"] = session_id
    suspects_interrogation[session_id] = [[] for _ in range(N_SUSPECTS)]

    page = flask.render_template(
        "index.html", n_suspects=N_SUSPECTS, language=language
    )
    return page if language == default_language else lang_translate(page, language)


@app.route("/img_scene")
@app.route("/img_suspect<int:nr>")
def get_image(nr=None):
    crime_id, _, _ = valid_session(nr)
    if not crime_id:
        return flask.abort(400)

    crime = generate_story(crime_id)
    if nr:
        prompt = prompts["img_suspect"]
        desc = crime["suspects_priv"][nr - 1]["image"]
    else:
        prompt = prompts["img_scene"]
        desc = crime["img_scene"]
    image_data = AI.send_message(prompt, crime_id, prompt=desc)
    response = flask.make_response(image_data)
    response.headers.set("Content-Type", "image/png")
    return response


@app.route("/story")
@app.route("/suspect<int:nr>")
@app.route('/culprit')
def story(nr=None):
    crime_id, language, session_id = valid_session(nr)
    if not crime_id:
        return flask.redirect("/")

    crime = generate_story(crime_id)
    route = flask.request.url[len(flask.request.url_root) :]
    if route == "story":
        kwargs = {"story": [crime["prologue"], crime["story"]]}
    elif route.startswith("suspect"):
        kwargs = {
            "suspect_prog": nr,
            "suspect_name": crime["suspects"][nr-1]["name"],
            "suspect_desc": crime["suspects"][nr-1]["description"],
            "questions": suspects_interrogation[session_id][nr -1],
            "max_questions": N_QUESTIONS,
            "max_question_chars": MAX_QUESTION_CHARS,
            "next_label": f"Sospetto successivo" if nr < N_SUSPECTS else "Smaschera il colpevole",
            "next_link": f"suspect{nr+1}" if nr < N_SUSPECTS else "culprit"
        }
    else:
        kwargs = {"suspects": crime["suspects"]}

    breadcrumb = (
        [
            {"href": "/", "label": "Inizio"},
            {"href": "story", "label": "Crimine"},
            {"href": "suspect1", "label": "Sospetto 1"},
        ]
        + [{"href": f"suspect{i}", "label": i} for i in range(2, N_SUSPECTS + 1)]
        + [
            {"href": "culprit", "label": "Colpevole"},
            {"href": "the_end", "label": "Fine"},
        ]
    )
    breadcrumb_active = next(
        idx for idx, obj in enumerate(breadcrumb) if obj.get("href") == route
    )
    return flask.render_template(
        "story.html",
        breadcrumb=breadcrumb,
        breadcrumb_active=breadcrumb_active,
        **kwargs,
    )


@app.route("/suspect_interrogation<int:nr>", methods=["POST"])
def suspect_interrogation(nr):
    crime_id, language, session_id = valid_session(nr)
    if not crime_id:
        return flask.abort(400)

    message = flask.request.json["message"]
    suspect = suspects_interrogation[session_id][nr -1]
    if len(suspect) >= N_QUESTIONS or not (0 < len(message) <= MAX_QUESTION_CHARS):
        return flask.abort(400)

    #TODO: analizzare 'message' per evitare che l'AI esca dal ruolo

    crime = generate_story(crime_id)
    params = deepcopy(prompts["suspect"])
    params["messages"][-1]["content"] = params["messages"][-1]["content"].format(
        crime["prologue"],
        crime["story"],
        crime["suspects"][nr - 1]["name"],
        crime["suspects"][nr - 1]["description"],
        crime["suspects_priv"][nr - 1]["image"],
        crime["culprit"]["clue"],
        crime["culprit"]["motive"],
    )
    for elem in suspect:
        params["messages"].append({"role": "user", "content": elem["question"]})
        params["messages"].append({"role": "assistant", "content": elem["response"]})
    params["messages"].append({"role": "user", "content": message})

    def generate():
        full_response = []
        for content in AI.stream_message(params):
            full_response.append(content)
            yield content.encode()
        suspect.append({"question": message, "response": ''.join(full_response)})

    return flask.Response(flask.stream_with_context(generate()), content_type='text/plain')



@app.route("/accuse<int:nr>")
def accuse(nr):
    _, _, session_id = valid_session(nr)
    if not session_id:
        return flask.abort(400)
    # TODO: verificare che l'interrogatorio sia finito?
    flask.session["alleged_culprit"] = nr - 1
    return flask.redirect(flask.url_for("the_end", story=session_id))


@app.route("/the_end")
def the_end():
    session_id = flask.request.args.get("story")
    try:
        user_session = end_session(session_id)
    except Exception:
        return flask.redirect("/")

    crime_id = user_session["crime_id"]
    crime = generate_story(crime_id)
    suspects = crime.pop("suspects")
    suspects_priv = crime.pop("suspects_priv")
    alleged_idx = int(user_session["alleged_culprit"])
    crime["alleged_culprit"] = suspects[alleged_idx]["name"]
    for idx, item in enumerate(suspects_priv):
        suspects[idx].update(item)
    for idx, item in enumerate(user_session["interrogation"]):
        suspects[idx]["interrogation"] = item

    image_data = AI.send_message(prompts["img_scene"], crime_id, prompt=crime["img_scene"])
    crime["img_scene"] = base64.b64encode(image_data).decode('utf-8')
    for item in suspects:
        image_data = AI.send_message(prompts["img_suspect"], crime_id, prompt=item["image"])
        item["image"] = base64.b64encode(image_data).decode('utf-8')

    return flask.render_template("the_end.html", crime=crime, suspects=suspects,
        story= [crime["prologue"], crime["story"]],
        share_link=flask.request.url)


@app.route("/show_logs")
def show_logs():
    return flask.render_template("logs.html", data=AI.logs())


@AI.cache
def crime_pool(n):
    return [secrets.token_hex(32) for _ in range(n)]


@AI.cache
def generate_crime_id(cache_hash):
    return secrets.token_hex(32)


def generate_story(crime_id):
    response = AI.send_message(prompts["story"], crime_id)
    crime = json.loads(response)
    crime["crime_id"] = crime_id
    return crime


@AI.cache
def end_session(session_id):
    result = {
        "crime_id": flask.session["crime_id"],
        "language": flask.session["language"],
        "alleged_culprit": flask.session["alleged_culprit"],
        "interrogation": suspects_interrogation.pop(session_id),
    }
    flask.session.clear()
    return result
