import hashlib, os, sys
SRC = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "..", "..", "src",
                   "airbyte-integrations", "connectors", "source-hubspot")
sys.path.insert(0, os.path.abspath(SRC))
import requests
from airbyte_cdk.sources.declarative.interpolation import InterpolatedString
import components

CONFIGS = [
    {"credentials": {"credentials_title": "Private App Credentials", "access_token": "tok"}},
    {"credentials": {"credentials_title": "OAuth Credentials", "client_id": "c", "client_secret": "s", "refresh_token": "r"}},
]
CODES = [200, 400, 401, 403, 404, 429, 500, 502, 503, 530]

def resp(code):
    r = requests.Response()
    r.status_code = code
    r._content = b'{"status":"error","message":"x"}' if code >= 400 else b'{"results":[]}'
    r.headers["Content-Type"] = "application/json"
    r.url = "https://api.hubapi.com/crm/v4/associations/contacts/companies/batch/read"
    r.request = requests.Request("POST", r.url).prepare()
    return r

h = hashlib.sha256()
responses = [resp(c) for c in CODES]
for it in range(300):
    for cfg in CONFIGS:
        retr = components.build_associations_retriever(
            associations_list=["companies", "deals"],
            parent_entity=InterpolatedString.create("contacts", parameters={}),
            config=cfg,
        )
        eh = retr.requester.error_handler
        for r in responses:
            res = eh.interpret_response(r)
            if it == 0:
                h.update(f"{cfg['credentials']['credentials_title']}|{r.status_code}|{res.response_action}|{res.failure_type}|{res.error_message}\n".encode())
        res = eh.interpret_response(requests.exceptions.ConnectionError("boom"))
        if it == 0:
            h.update(f"exc|{res.response_action}|{res.failure_type}\n".encode())
print(h.hexdigest())
