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

from copy import deepcopy
from datetime import datetime
from functools import wraps as fn_wraps
import json
import requests
import openai
import boto3
import redis

# Automatically detect the region when running on EC2
try:
    token_url = "http://169.254.169.254/latest/api/token"
    token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    token_response = requests.put(token_url, headers=token_headers)
    token = token_response.text
    metadata_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    metadata_headers = {"X-aws-ec2-metadata-token": token}
    metadata_response = requests.get(metadata_url, headers=metadata_headers)
    metadata = json.loads(metadata_response.text)
    region_name = metadata["region"]
except Exception:
    region_name = "dummy"
boto3.setup_default_session(region_name=region_name)


class Cache:
    def __init__(self, conn, **kwargs):
        if isinstance(conn, str):
            if conn.startswith("dynamodb."):
                # Extract the table name from 'dynamodb.tablename'
                table_name = conn.split(".", 1)[1]
                self.cache = DynamoDBCacheImpl(table_name, **kwargs)
                self.logs = self.cache
            elif conn.startswith("redis"):
                self.cache = RedisCacheImpl(redis.Redis.from_url(conn, **kwargs))
                self.logs = self.cache
        elif isinstance(conn, dict):
            self.cache = conn
            self.logs = []
        else:
            raise ValueError("Unsupported cache backend")

    def __call__(self, fn):
        @fn_wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"_fn_{fn.__name__}_{str(args)}_{str(kwargs)}"
            result = self.cache.get(key)
            if result is None:
                result = fn(*args, **kwargs)
                log_message = {
                    "event": f"_fn_{fn.__name__}_{str(args)}_{str(kwargs)}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "log": str(type(result))
                }
                try:
                    log_message["log"] = f"{len(result)} bytes" if isinstance(result, bytes) else json.dumps(result)
                    self.cache[key] = result
                except Exception:
                    pass
                self.logs.log_append(log_message)
            return result

        return wrapper

    def log_dump(self):
        if isinstance(self.logs, list):
            return {"_log_data": self.logs}
        return self.logs.log_dump()


class RedisCacheImpl:
    def __init__(self, conn, **kwargs):
        self.conn = conn

    def get(self, key):
        value = self.conn.get(key)
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def __setitem__(self, key, value):
        if not isinstance(value, bytes):
            value = json.dumps(value)
        return self.conn.set(key, value)

    def log_append(self, log_message):
        self.conn.rpush("_log_data", json.dumps(log_message))

    def log_dump(self):
        result = {}
        for key in self.conn.keys("_log*"):
            result[key] = [json.loads(v) for v in self.conn.lrange(key, 0, -1)]
        return result


class DynamoDBCacheImpl:
    def __init__(self, table_name, **kwargs):
        self.dynamodb = boto3.resource("dynamodb", **kwargs)
        self.table = self.dynamodb.Table(table_name)

    def get(self, key):
        key = key[:2000]
        response = self.table.get_item(Key={"ID": key})
        value = response.get("Item", {}).get("data")
        if value is None:
            return value
        if "B" in value:
            return bytes(value["B"])
        return boto3.dynamodb.types.TypeDeserializer().deserialize(value)

    def __setitem__(self, key, value):
        key = key[:2000]
        value = boto3.dynamodb.types.TypeSerializer().serialize(value)
        self.table.put_item(Item={"ID": key, "data": value})

    def _increment_log_counter(self):
        log_counter_key = "_log_counter"
        response = self.table.update_item(
            Key={"ID": log_counter_key},
            UpdateExpression="ADD item_data :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return response["Attributes"]["item_data"]

    def log_append(self, log_message):
        log_key = f"_log_data_{self._increment_log_counter()}"
        return self.__setitem__(log_key, log_message)

    def log_dump(self):
        keys = []
        scan_kwargs = {
            "ExpressionAttributeNames": {"#k": "ID"},
            "ProjectionExpression": "#k",
            "FilterExpression": boto3.dynamodb.conditions.Attr("ID").begins_with(
                "_log_data_"
            ),
        }
        while True:
            response = self.table.scan(**scan_kwargs)
            keys.extend(response.get("Items", []))
            scan_kwargs["ExclusiveStartKey"] = response.get("LastEvaluatedKey")
            if not scan_kwargs["ExclusiveStartKey"]:
                break

        keys.sort(key=lambda x: int(x["ID"].split("_")[-1]))
        keys = keys[-50:]
        if not keys:
            return {"log_data": []}

        request_items = {self.table.name: {"Keys": [{"ID": key_item["ID"]} for key_item in keys]}}
        batch_response = self.dynamodb.batch_get_item(RequestItems=request_items)
        log_items = batch_response["Responses"][self.table.name]
        log_items.sort(key=lambda x: int(x["ID"].split("_")[-1]))
        decoder = boto3.dynamodb.types.TypeDeserializer()

        return {"log_data": [decoder.deserialize(item["data"]) for item in log_items]}


class AI:
    cache = Cache({})
    if openai.api_key is None:
        try:
            response = boto3.client("ssm").get_parameter(
                Name="OPENAI_API_KEY", WithDecryption=True
            )
            openai.api_key = response["Parameter"]["Value"]
        except Exception:
            pass

    @staticmethod
    def set_cache(conn, **kwargs):
        new_cache = Cache(conn, **kwargs)
        AI.cache.cache = new_cache.cache
        AI.cache.logs = new_cache.logs

    @staticmethod
    def logs():
        return AI.cache.log_dump()

    @staticmethod
    @cache
    def stream_message(params):
        response = openai.ChatCompletion.create(**params)
        for chunk in response:
            content = chunk['choices'][0]['delta'].get('content')
            if content is not None:
                yield content

    @staticmethod
    def send_message(params, cache_prefix="", **kwargs):
        params = deepcopy(params)
        for key, value in kwargs.items():
            keys = key.split("__")
            last_key = keys[-1]
            target = params
            for sub_key in keys[:-1]:
                if isinstance(target, list):
                    target = target[-1]
                target = target[sub_key]
            if isinstance(target, list):
                target = target[-1]
            if isinstance(value, list):
                value = tuple(value)
            elif not isinstance(value, tuple):
                value = (value,)
            target[last_key] = target[last_key].format(*value)
        return AI._openai_send_message(params, cache_prefix)

    @staticmethod
    @cache
    def _openai_send_message(params, cache_prefix):
        response = AI._openai_send_request(params, cache_prefix)
        if "data" in response:
            url = response["data"][0]["url"]
            data = requests.get(url).content
            return data

        if "message" in response["choices"][0]:
            return response["choices"][0]["message"]["content"]

        return response["choices"][0]["text"]

    @staticmethod
    @cache
    def _openai_send_request(params, cache_prefix):
        try:
            if "messages" in params:
                return openai.ChatCompletion.create(**params)
            if "engine" in params:
                return openai.Completion.create(**params)

            return openai.Image.create(**params)
        except Exception as e:
            AI._openai_log_error(
                timestamp=datetime.now(),
                fn="_openai_send_request",
                params=params,
                cache_prefix=cache_prefix,
                exception=e,
            )
            raise

    @staticmethod
    @cache
    def _openai_log_error(**kwargs):
        return True
