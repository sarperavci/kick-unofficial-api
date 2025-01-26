# Run: mitmproxy -s misc/endpoint_discovery.py -p 8080 -q

from mitmproxy import ctx
import json, os

target_site = "kick.com"
api_docs_dir = "api_docs"

if not os.path.exists(api_docs_dir):
    os.makedirs(api_docs_dir)


def request(flow):
    if target_site in flow.request.pretty_url and "api" in flow.request.pretty_url:
        print("\n" + "=" * 50)
        print(f"API Request: {flow.request.pretty_url}")
        print(f"Method: {flow.request.method}")

        if flow.request.method in ["POST", "PUT", "PATCH"]:
            try:
                if flow.request.text:
                    json_data = json.loads(flow.request.text)
                    print("\nRequest Body:")
                    print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                print(f"\nRequest Body: {flow.request.text}")


def response(flow):
    if target_site in flow.request.pretty_url and "api" in flow.request.pretty_url:
        if flow.response and flow.response.status_code:
            print(f"\nResponse Status: {flow.response.status_code}")
            try:
                if flow.response.text:
                    json_data = json.loads(flow.response.text)
                    print("\nResponse Body:")
                    print(json.dumps(json_data, indent=2))
                    with open(
                        f"{api_docs_dir}/{flow.request.method}_{flow.request.path.replace('/', '_')}.txt",
                        "w",
                    ) as f:
                        f.write(
                            f"{flow.request.method} {flow.request.path}\n"
                            + f"req_body: {flow.request.text}\n"
                            + f"res_body: {json.dumps(json_data, indent=2)}"
                        )
            except json.JSONDecodeError:
                print(f"\nResponse Body: {flow.response.text}")
            print("=" * 50 + "\n")
